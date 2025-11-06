# Architecture Diagram: Refactored Claude Processor

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Langflow System                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         ClaudeProcessor (Thin Adapter)                    │  │
│  │  - Parse Langflow inputs → Config                         │  │
│  │  - Build dependencies                                      │  │
│  │  - Delegate to Pipeline                                    │  │
│  │  - Convert result → Langflow Data                         │  │
│  └──────────────────────┬────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │   ProcessingPipeline           │
         │   (Orchestrator)               │
         │  - Validate input              │
         │  - Coordinate services         │
         │  - Process loop                │
         │  - Generate summary            │
         └───┬────────┬────────┬──────┬───┘
             │        │        │      │
    ┌────────┘        │        │      └────────┐
    ▼                 ▼        ▼               ▼
┌─────────┐     ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Logger  │     │  Page    │ │  Page    │ │ Config   │
│ Facade  │     │Processor │ │ Limiter  │ │ Objects  │
└────┬────┘     └─────┬────┘ └────┬─────┘ └──────────┘
     │                │           │
     │                │           │
     ▼                ▼           ▼
┌─────────┐     ┌──────────┐ ┌──────────┐
│ Session │     │ API      │ │ Counter  │
│ Logger  │     │ Client   │ │ State    │
│         │     │          │ │          │
│ CLI     │     │ Retry    │ │ Skip     │
│ Output  │     │ Handler  │ │ Messages │
└─────────┘     │          │ └──────────┘
                │ Prompt   │
                │ Factory  │
                │          │
                │ Variety  │
                │ Tracker  │
                └──────────┘
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT: Langflow Pages (List[Data])                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  1. Parse Configuration │
         │  ┌──────────────────┐  │
         │  │ PipelineConfig   │  │
         │  │ - theme          │  │
         │  │ - difficulty     │  │
         │  │ - model          │  │
         │  │ - limits         │  │
         │  │ - seed           │  │
         │  └──────────────────┘  │
         └────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  2. Initialize Services │
         │  ┌──────────────────┐  │
         │  │ LoggerFacade     │  │
         │  │ PageLimiter      │  │
         │  │ PageProcessor    │  │
         │  │ Pipeline         │  │
         │  └──────────────────┘  │
         └────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  3. Validate Input      │
         │  - Check pages exist    │
         │  - Check not empty      │
         │  - Log summary          │
         └────────────┬───────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  4. Processing Loop                    │
         │                                        │
         │  For each page:                        │
         │    ┌───────────────────────────────┐   │
         │    │ 4a. Check Limits              │   │
         │    │   - Total pages limit?        │   │
         │    │   - Topic limit reached?      │   │
         │    │   ├─ No  → Continue           │   │
         │    │   └─ Yes → Skip & Log         │   │
         │    └──────────────┬────────────────┘   │
         │                   ▼                     │
         │    ┌───────────────────────────────┐   │
         │    │ 4b. Process Single Page       │   │
         │    │   - Build prompt              │   │
         │    │   - Call API (with retry)     │   │
         │    │   - Parse response            │   │
         │    │   - Track variety             │   │
         │    │   - Merge results             │   │
         │    └──────────────┬────────────────┘   │
         │                   ▼                     │
         │    ┌───────────────────────────────┐   │
         │    │ 4c. Update Counters           │   │
         │    │   - Mark topic processed      │   │
         │    │   - Increment total           │   │
         │    │   - Log progress              │   │
         │    └───────────────────────────────┘   │
         └────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  5. Finalize            │
         │  - Sort by page number  │
         │  - Dump JSON (if set)   │
         │  - Save logs            │
         │  - Generate summary     │
         └────────────┬───────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT: PipelineResult → List[Data]                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Dependencies

```
┌────────────────────────────────────────────────────────────────┐
│  Langflow Layer                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  components/claude_processor.py                          │  │
│  │  - ClaudeProcessor(Component)                            │  │
│  └────────────────────────┬─────────────────────────────────┘  │
└───────────────────────────┼────────────────────────────────────┘
                            │
                            │ uses
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  Business Logic Layer                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  components/processor/                                   │  │
│  │  ┌────────────────┐  ┌────────────────┐                  │  │
│  │  │ pipeline.py    │  │ page_processor │                  │  │
│  │  │                │  │     .py        │                  │  │
│  │  │ Processing     │  │                │                  │  │
│  │  │ Pipeline       │  │ PageProcessor  │                  │  │
│  │  └───────┬────────┘  └───────┬────────┘                  │  │
│  │          │                   │                            │  │
│  │          │ uses              │ uses                       │  │
│  │          ▼                   ▼                            │  │
│  │  ┌────────────────┐  ┌────────────────┐                  │  │
│  │  │ limiter.py     │  │logger_facade.py│                  │  │
│  │  │                │  │                │                  │  │
│  │  │ PageLimiter    │  │ LoggerFacade   │                  │  │
│  │  └────────────────┘  └────────────────┘                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            │ uses
                            ▼
┌────────────────────────────────────────────────────────────────┐
│  Infrastructure Layer                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ components/  │  │ components/  │  │ components/  │         │
│  │   api/       │  │   prompts/   │  │  tracking/   │         │
│  │              │  │              │  │              │         │
│  │ ClaudeAPI    │  │ Prompt       │  │ Variety      │         │
│  │ Client       │  │ Factory      │  │ Tracker      │         │
│  │              │  │              │  │              │         │
│  │ RetryHandler │  │ Strategies   │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │ components/  │  │ components/  │                           │
│  │  config/     │  │  logging/    │                           │
│  │              │  │              │                           │
│  │ Theme        │  │ Session      │                           │
│  │ Difficulty   │  │ Logger       │                           │
│  │ Limits       │  │              │                           │
│  │              │  │ Output       │                           │
│  │              │  │ Dumper       │                           │
│  └──────────────┘  └──────────────┘                           │
└────────────────────────────────────────────────────────────────┘
```

---

## Responsibility Mapping

### Before Refactoring

```
ClaudeProcessor (570 lines)
├── Langflow setup (150 lines)
├── Configuration parsing (100 lines)
├── API communication (40 lines)
├── Prompt dispatch (60 lines)
├── Pipeline orchestration (200 lines)
└── Logging (scattered throughout)
```

### After Refactoring

```
ClaudeProcessor (150 lines)
└── Langflow adapter only
    ├── Input/output definitions
    ├── Config parsing
    ├── Dependency injection
    └── Result conversion

ProcessingPipeline (200 lines)
└── Orchestration only
    ├── Validation
    ├── Processing loop
    ├── Coordination
    └── Finalization

PageProcessor (150 lines)
└── Single page processing
    ├── Prompt building
    ├── API calls
    ├── Result merging
    └── Variety tracking

PageLimiter (120 lines)
└── Limit enforcement
    ├── Limit checking
    ├── Counter management
    ├── Skip tracking
    └── Summary generation

LoggerFacade (100 lines)
└── Unified logging
    ├── CLI output
    ├── Session logging
    ├── Progress indicators
    └── Summary formatting
```

---

## Testing Strategy Visualization

```
┌─────────────────────────────────────────────────────────────┐
│  Test Pyramid                                               │
│                                                             │
│                    ┌───────────────┐                        │
│                    │  Integration  │  (5 tests)             │
│                    │   Tests       │  - Full pipeline       │
│                    │               │  - Mock API only       │
│                    └───────────────┘                        │
│                                                             │
│              ┌─────────────────────────┐                    │
│              │   Component Tests       │  (10 tests)        │
│              │  - Langflow adapter     │  - Real config     │
│              │  - Pipeline run()       │  - Mock services   │
│              └─────────────────────────┘                    │
│                                                             │
│      ┌───────────────────────────────────────────┐          │
│      │         Unit Tests                        │ (50+)    │
│      │  - LoggerFacade (10)                      │          │
│      │  - PageLimiter (15)                       │          │
│      │  - PageProcessor (15)                     │          │
│      │  - Pipeline methods (10)                  │          │
│      └───────────────────────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Test Coverage Target: 95%+
Fast tests: 90% (unit + component)
Slow tests: 10% (integration)
```

---

## Error Handling Flow

```
┌──────────────────────────────────────────────────────────┐
│  Error Handling Strategy                                 │
└──────────────────────────────────────────────────────────┘

Input Validation Errors
    │
    ├─→ Empty pages
    │       └─→ LoggerFacade.error()
    │           └─→ Return empty result
    │
    └─→ Invalid config
            └─→ LoggerFacade.error()
                └─→ Use defaults + warn

API Errors (per page)
    │
    ├─→ Retry-able (timeout, rate limit)
    │       └─→ RetryHandler (exponential backoff)
    │           ├─→ Success → Continue
    │           └─→ Fail → Log + Return error page
    │
    └─→ Non-retryable (auth, invalid request)
            └─→ Log error
                └─→ Return error page
                    └─→ Continue with next page

Processing Errors (per page)
    │
    ├─→ Parse error
    │       └─→ Log + Return error page
    │
    ├─→ Limit reached
    │       └─→ Log skip reason
    │           └─→ Continue with next page
    │
    └─→ Unexpected exception
            └─→ Log stack trace
                └─→ Return error page
                    └─→ Continue with next page

Strategy: Fail per-page, not per-batch
Result: Partial success possible
```

---

## Configuration Flow

```
┌──────────────────────────────────────────────────────────┐
│  Configuration Parsing                                   │
└──────────────────────────────────────────────────────────┘

Langflow Inputs
    ├─→ anthropic_api_key (SecretStrInput)
    ├─→ model_name (MessageTextInput)
    ├─→ difficulty (MessageTextInput)
    ├─→ random_seed (MessageTextInput)
    ├─→ max_total_pages (MessageTextInput)
    ├─→ pages_per_topic (MessageTextInput)
    └─→ dummy_output_dir (MessageTextInput)
            │
            ▼
┌────────────────────────────────┐
│  ClaudeProcessor._build_config()│
│                                │
│  ┌──────────────────────────┐  │
│  │ Parse & Validate         │  │
│  │  - ThemeConfig           │  │
│  │  - DifficultyConfig      │  │
│  │  - PageLimitsConfig      │  │
│  └──────────────────────────┘  │
│            │                   │
│            ▼                   │
│  ┌──────────────────────────┐  │
│  │ Build Config Objects     │  │
│  │  - PipelineConfig        │  │
│  │  - ProcessorConfig       │  │
│  │  - LimiterConfig         │  │
│  └──────────────────────────┘  │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│  Inject into Services          │
│                                │
│  ProcessingPipeline(config)    │
│  PageProcessor(config)         │
│  PageLimiter(config)           │
└────────────────────────────────┘
```

---

## Performance Considerations

```
┌──────────────────────────────────────────────────────────┐
│  Performance Optimization Points                         │
└──────────────────────────────────────────────────────────┘

1. Lazy Initialization
   - Only create services when needed
   - Don't initialize API client until first call

2. Batching Opportunities
   - Could batch API calls (future optimization)
   - Currently sequential for simplicity

3. Caching
   - Prompt strategies could cache built prompts
   - Theme sanitization could cache results

4. Parallel Processing
   - Pages are independent
   - Could process N pages concurrently
   - Would need async/await refactor

5. Memory Management
   - Stream logs to disk vs. in-memory
   - Limit variety tracker history

Current Performance:
- Sequential processing: ~2s/page
- With 20 pages: ~40s total
- Network bound (API calls)

Future Performance (with async):
- Parallel processing: ~2s for 5 pages
- With 20 pages: ~8s total (5 concurrent)
- Same network bound but better utilization
```

---

## Glossary

**ClaudeProcessor**: Thin Langflow component adapter
**ProcessingPipeline**: Main orchestrator for processing flow
**PageProcessor**: Single-page processing service
**PageLimiter**: Limit enforcement service
**LoggerFacade**: Unified logging interface
**PipelineConfig**: Configuration value object for pipeline
**PipelineResult**: Result value object with metadata
**ProcessedPage**: Single page result (success or error)

---

## Key Design Decisions

1. **Dependency Injection**: All services receive dependencies via constructor
2. **Value Objects**: Config and result are immutable data structures
3. **Service Layer**: Business logic separated from infrastructure
4. **Fail-Safe**: Page errors don't stop the batch
5. **Observable**: Comprehensive logging at each layer
6. **Testable**: Pure functions and mockable interfaces

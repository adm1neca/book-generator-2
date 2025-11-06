# Testing Activity Renderers

This document describes how to test the individual activity page renderers.

## Test Script

The `test_activities.py` script allows you to test each activity type independently and generate sample PDFs for verification.

### Prerequisites

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Usage

#### List Available Test Activities

```bash
python test_activities.py --list
```

#### Test All Activities

Run all activity tests and generate PDFs:

```bash
python test_activities.py --all
```

This will:
- Create a `test_output/` directory
- Generate test PDFs for each activity type
- Show a summary of passed/failed tests

#### Test Specific Activity

Test a single activity:

```bash
python test_activities.py --activity matching
```

#### Enable Debug Logging

Get detailed logging information:

```bash
python test_activities.py --activity maze --debug
```

### Test Output

All test PDFs are saved to the `test_output/` directory with names like:
- `test_matching.pdf`
- `test_maze.pdf`
- `test_dot_to_dot.pdf`
- `test_tracing.pdf`

## Logging

All activity renderers now include comprehensive logging at key points.

### Log Levels

- **INFO**: High-level activity status
- **DEBUG**: Detailed information (coordinates, sizes)
- **WARNING**: Non-critical issues (fallbacks, missing renderers)
- **ERROR**: Critical failures

## Troubleshooting

### Issue: "Only showing dots, no shapes"

Check the logs for warnings about missing shape renderers.

### Issue: "Maze has no clear path"

Check logs for maze generation statistics (cells visited, walls removed).

### Issue: "Connect the dots is empty"

Check logs for dot generation messages.

### Issue: "Tracing shows text instead of shapes"

Check logs for content type detection.

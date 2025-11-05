from langflow.custom import Component
from langflow.io import Output, DataInput, MessageTextInput
from langflow.schema import Data
from typing import List
import json
import subprocess
from datetime import datetime
import os

class PDFGenerator(Component):
    display_name = "PDF Generator"
    description = "Generates PDF from processed pages"
    icon = "file-text"

    inputs = [
        DataInput(
            name="processed_pages",
            display_name="Processed Pages",
            info="Pages with Claude-generated content",
            is_list=True
        ),
        MessageTextInput(
            name="script_path",
            display_name="Script Path",
            value="/app/activity_generator.py",
            info="Path to the PDF generation script"
        ),
    ]

    outputs = [
        Output(display_name="PDF Info", name="pdf_info", method="generate_pdf"),
    ]

    def generate_pdf(self) -> Data:
        # Prepare data
        pages = [page.data for page in self.processed_pages]
        
        # Sort by page number
        pages.sort(key=lambda x: x.get('pageNumber', 0))
        
        # Generate filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f'/tmp/booklet_{timestamp}.json'
        pdf_file = f'/tmp/booklet_{timestamp}.pdf'
        
        # Write JSON file
        with open(json_file, 'w') as f:
            json.dump(pages, f, indent=2)
        
        self.status = f"JSON written to {json_file}"
        
        # Execute Python script
        try:
            cmd = ['python3', self.script_path, json_file, pdf_file]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check if PDF was created
            if os.path.exists(pdf_file):
                file_size = os.path.getsize(pdf_file)
                self.status = f"PDF generated successfully! Size: {file_size} bytes"
                
                return Data(data={
                    'success': True,
                    'pdf_file': pdf_file,
                    'json_file': json_file,
                    'total_pages': len(pages),
                    'file_size': file_size,
                    'message': f'PDF created: {pdf_file}',
                    'stdout': result.stdout
                })
            else:
                return Data(data={
                    'success': False,
                    'error': 'PDF file not created',
                    'stdout': result.stdout,
                    'stderr': result.stderr
                })
                
        except subprocess.CalledProcessError as e:
            self.status = "PDF generation failed!"
            return Data(data={
                'success': False,
                'error': e.stderr,
                'message': 'PDF generation failed',
                'stdout': e.stdout
            })
        except Exception as e:
            return Data(data={
                'success': False,
                'error': str(e),
                'message': 'Unexpected error'
            })
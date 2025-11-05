from langflow.custom import Component
from langflow.io import Output, DataInput
from langflow.schema import Data
from typing import List
import sys
import os

class PDFGenerator(Component):
    display_name = "PDF Generator"
    description = "Generates PDF booklet from processed activity pages"
    icon = "file-text"

    inputs = [
        DataInput(
            name="processed_pages",
            display_name="Processed Pages",
            info="List of processed page specifications from Claude",
            is_list=True
        ),
    ]

    outputs = [
        Output(display_name="PDF Info", name="pdf_info", method="generate_pdf"),
    ]

    def generate_pdf(self) -> Data:
        """Generate PDF from processed pages"""
        print("="*60)
        print("📄 PDF GENERATOR STARTED")
        print("="*60)

        try:
            # Import activity_generator here to avoid module-level import issues
            scripts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
            if scripts_path not in sys.path:
                sys.path.insert(0, scripts_path)

            print(f"📂 Looking for activity_generator in: {scripts_path}")

            try:
                from activity_generator import generate_booklet
                print("✅ activity_generator imported successfully")
            except ImportError as e:
                error_msg = f"Failed to import activity_generator: {str(e)}"
                print(f"❌ {error_msg}")
                print(f"   sys.path: {sys.path}")
                print(f"   __file__: {__file__}")
                self.status = "Import error"
                return Data(data={
                    'success': False,
                    'error': error_msg,
                    'scripts_path': scripts_path
                })
            # Validate input
            if not self.processed_pages:
                error_msg = "No pages provided to generate PDF"
                print(f"❌ ERROR: {error_msg}")
                self.status = error_msg
                return Data(data={
                    'success': False,
                    'error': error_msg
                })

            pages_count = len(self.processed_pages)
            print(f"📊 Received {pages_count} pages to generate PDF")

            # Convert Data objects to dictionaries
            pages_data = []
            for idx, page_obj in enumerate(self.processed_pages):
                page_dict = page_obj.data if hasattr(page_obj, 'data') else page_obj
                pages_data.append(page_dict)
                print(f"  Page {idx + 1}: {page_dict.get('type', 'unknown')} - {page_dict.get('title', 'No title')}")

            # Generate output filename
            output_file = '/tmp/activity_booklet.pdf'
            print(f"\n🎯 Generating PDF: {output_file}")

            self.status = f"Generating PDF with {pages_count} pages..."

            # Generate the PDF using the script
            generate_booklet(pages_data, output_file)

            # Verify file was created
            if not os.path.exists(output_file):
                error_msg = f"PDF generation completed but file not found at {output_file}"
                print(f"❌ ERROR: {error_msg}")
                self.status = "PDF generation failed"
                return Data(data={
                    'success': False,
                    'error': error_msg
                })

            file_size = os.path.getsize(output_file)
            print(f"✅ PDF generated successfully!")
            print(f"   File: {output_file}")
            print(f"   Size: {file_size:,} bytes")
            print(f"   Pages: {pages_count}")
            print("="*60)

            self.status = f"✓ PDF generated: {pages_count} pages, {file_size:,} bytes"

            return Data(data={
                'success': True,
                'pdf_file': output_file,
                'file_size': file_size,
                'total_pages': pages_count,
                'message': f'PDF generated successfully with {pages_count} pages'
            })

        except Exception as e:
            error_msg = f"PDF generation error: {str(e)}"
            print(f"❌ ERROR: {error_msg}")
            import traceback
            traceback.print_exc()

            self.status = "PDF generation failed"
            return Data(data={
                'success': False,
                'error': error_msg,
                'traceback': traceback.format_exc()
            })

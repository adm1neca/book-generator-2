from langflow.custom import Component
from langflow.io import Output, DataInput
from langflow.schema import Data
import base64


class PDFDownloader(Component):
    display_name = "PDF Downloader"
    description = "Reads PDF file and provides download link"
    icon = "download"

    inputs = [
        DataInput(
            name="pdf_info",
            display_name="PDF Info",
            info="Information about generated PDF"
        ),
    ]

    outputs = [
        Output(display_name="Result", name="result", method="read_pdf"),
    ]

    def read_pdf(self) -> Data:
        pdf_info = self.pdf_info
        if isinstance(pdf_info, list):
            if not pdf_info:
                self.status = "No PDF info received"
                return Data(
                    data={
                        'success': False,
                        'error': 'No PDF info provided'
                    }
                )
            pdf_info = pdf_info[0]

        pdf_data = pdf_info.data

        if not pdf_data.get('success'):
            self.status = "PDF generation failed"
            return Data(
                data={
                    'success': False,
                    'error': pdf_data.get('error', 'Unknown error')
                }
            )

        pdf_file = pdf_data['pdf_file']

        try:
            with open(pdf_file, 'rb') as file_handle:
                pdf_bytes = file_handle.read()

            self.status = "PDF ready! File: {}".format(pdf_file)

            return Data(
                data={
                    'success': True,
                    'pdf_file': pdf_file,
                    'file_size': len(pdf_bytes),
                    'total_pages': pdf_data.get('total_pages', 30),
                    'download_message': 'PDF saved to: {}'.format(pdf_file),
                    'instructions': 'Download from container: docker cp langflow-custom:{} ./booklet.pdf'.format(pdf_file)
                }
            )

        except Exception as error:
            self.status = "Failed to read PDF"
            return Data(
                data={
                    'success': False,
                    'error': str(error)
                }
            )

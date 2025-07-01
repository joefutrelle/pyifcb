from zipfile import ZipFile

from PIL import Image
import pandas as pd
from io import BytesIO

import ifcb


def to_ecotaxa(b, zip_path=None):

    if zip_path is None:
        zip_path = f'{b.lid}.zip'

    with ZipFile(zip_path, 'w') as fout:
        records = []

        for roi_number, image_data in b.images.items():

            object_id = ifcb.Pid(b.lid).with_target(roi_number)
            img_file_name = f'{object_id}.png'

            record = {
                'sample_id': b.lid,
                'object_id': object_id,
                'img_file_name': img_file_name,
                'object_date': b.timestamp.strftime('%Y%m%d'),
                'object_time': b.timestamp.strftime('%H%M%S'),
            }

            records.append(record)

            image = Image.fromarray(image_data)
            
            # Convert the image to bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Write the bytes to the zip file
            fout.writestr(img_file_name, img_byte_arr)
    
        df = pd.DataFrame(records)
        buffer = BytesIO()
        tsv_filename = f'ecotaxa_metadata.tsv'
        df = pd.DataFrame(records)
        buffer = BytesIO()
        buffer.write('\t'.join(df.columns).encode() + b'\n')
        buffer.write('\t'.join('[t]' for _ in range(3)).encode() + b'\t')
        buffer.write('\t'.join('[f]' for _ in range(len(df.columns) - 3)).encode() + b'\n')
        df.to_csv(buffer, sep='\t', index=False, header=None)

        fout.writestr('ecotaxa_metadata.tsv', buffer.getvalue())

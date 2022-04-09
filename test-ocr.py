import easyocr
import os
# os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

if __name__ == '__main__':
    reader = easyocr.Reader(['en'])
    image = f'D:\\temp_ocr\\test_b.jpg'
    result = reader.readtext(image)
    print()
```sh
brew install youtube-dl
youtube-dl https://youtu.be/gGkhmrg7zKA -f worst

```


# install opencv
pip install --upgrade pip
pip install opencv-python


# install tessaract
brew install tesseract
pip install pytesseract

# install textract for japanese
download files. see : https://dev.classmethod.jp/articles/ocr-on-a-mac-device-with-pytesseract/

brew list tesseract

mv ~/Downloads/jpn.traineddata /opt/homebrew/Cellar/tesseract/5.3.2_1/share/tessdata/jpn.traineddata
mv ~/Downloads/jpn_vert.traineddata /opt/homebrew/Cellar/tesseract/5.3.2_1/share/tessdata/jpn_vert.traineddata

tesseract --list-langs


# install pytube
# pip install pytube
git clone https://github.com/kj-9/pytube.git _pytube
cd _pytube
python -m pip install -e .


# install
```
# https://stackoverflow.com/questions/76379293/how-can-i-fix-the-error-in-pymupdf-when-installing-paddleocr-with-pip
pip install "paddleocr>=2.0.1" --upgrade PyMuPDF==1.21.1
```
brew install mupdf swig freetype
pip install https://github.com/pymupdf/PyMuPDF/archive/master.tar.gz

-> not working


# install easyocr

if _lzma not found error, install xz and rebuild python
```
brew install xz
see also: https://qiita.com/NOIZE/items/13cad682d089db86d840
pyenv uninstall 3.9.6
pyenv install 3.9.6

pip install easyocr
```

Once built, the application can be found in dist/

## MacOS/Linux:
1. make the python virtual environment:

<code>python -m venv dfu_venv</code>


2. Jump into the virtual environment

<code>source dfu_env/bin/activate</code>


3. install dependencies

<code>pip install activate intelhex threading
brew install python-tk</code>

4. Build it

<code>pyinstaller --onefile --windowed --add-binary "/usr/local/bin/dfu-util:." --hidden-import=tkinter --hidden-import=ttk --hidden-import=threading --hidden-import=intelhex --clean Uploader.py</code>




## Windows:
1. make the virtual environment:

<code>python -m venv dfu_venv</code>


2. Jump into the virtual environment

<code>dfu_venv\Scripts\activate.bat</code>


3. install dependencies

Download the dfu-util.exe and place it into this folder if it is not already in this folder: <link>http://dfu-util.sourceforge.net/releases/dfu-util-0.8-binaries/win32-mingw32/dfu-util-static.exe</link>
<code>pip install activate intelhex</code>

4. Build it

<code>pyinstaller --onefile --windowed --add-binary "dfu-util.exe;." --hidden-import=tkinter --hidden-import=ttk --hidden-import=threading --hidden-import=intelhex --clean Uploader.py</code>


---


Once everything is installed and if you want to make adjustments to the app and re-build it, do this:

MacOs:
<code>source dfu_env/bin/activate

pyinstaller --onefile --windowed --add-binary "/usr/local/bin/dfu-util:." --hidden-import=tkinter --hidden-import=ttk --hidden-import=threading --hidden-import=intelhex --clean Uploader.py</code>


Windows:
<code>dfu_venv\Scripts\activate.bat

pyinstaller --onefile --windowed --add-binary "dfu-util.exe;." --hidden-import=tkinter --hidden-import=ttk --hidden-import=threading --hidden-import=intelhex --clean Uploader.py</code>

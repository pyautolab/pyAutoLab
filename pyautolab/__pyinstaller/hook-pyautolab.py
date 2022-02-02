from pathlib import Path

import pyautolab

pyautolab_path = Path(pyautolab.__file__).parent

datas = []
datas += [(str(pyautolab_path / "plugins"), "pyautolab/plugins")]
datas += [(str(pyautolab_path / "default.json"), "pyautolab")]

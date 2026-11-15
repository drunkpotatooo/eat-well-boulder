from pathlib import Path
import sys
import json
import platform

PARENT_DIR = Path(__file__).resolve().parent
HOST_NAME = 'store_bought_host'
HOST_SCRIPT = PARENT_DIR / 'host.py'


def build_host_manifest(exec_path):
	return {
		'name': HOST_NAME,
		'description': 'Store Bought local SQLite storage host',
		'path': str(exec_path),
		'type': 'stdio',
		'allowed_extensions': ['@storebought'],
	}


def register_host_windows():
	import winreg

	# .bat wrapper because the registry manifest must point at a Windows executable for some reason
	wrapper = PARENT_DIR / f'{HOST_NAME}.bat'
	wrapper.write_text(f'@echo off\r\n"{sys.executable}" "{HOST_SCRIPT}"\r\n')
	manifest_path = PARENT_DIR / f'{HOST_NAME}.json'
	manifest_path.write_text(json.dumps(build_host_manifest(wrapper), indent='\t'))

	# windows needs this to be put into registry, again for some reason I'm not really sure about but whatever
	key_path = f'Software\\Mozilla\\NativeMessagingHosts\\{HOST_NAME}'
	with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
		winreg.SetValueEx(key, None, 0, winreg.REG_SZ, str(manifest_path))
	print(f'Registered native messaging host at HKEY_CURRENT_USER\\{key_path}')


if __name__ == '__main__':
	if platform.system() == 'Windows': register_host_windows()
	else: print('Platform not supported for now. I\'ll get to it, maybe.')

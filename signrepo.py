import os
import sys
import subprocess

OPENSSL_PATH='openssl'
SIG_EXTN='.sig'

def usage():
	print sys.argv[0], '<sign_cert> <key>'

if len(sys.argv) < 3:
	usage()
	print 'error: must include path to signing certificate and private key'
	sys.exit(1)

cert_path = sys.argv[1]

if not os.path.isfile(cert_path):
	usage()
	print 'error: certificate must be a file'
	sys.exit(1)

key_path = sys.argv[2]

if not os.path.isfile(key_path):
	usage()
	print 'error: certificate must be a file'
	sys.exit(1)


for thepath in ('manifests', 'catalogs'):
	for dirpath, dirnames, filenames in os.walk(thepath):
		for filename in filenames:
			filepath = os.path.join(dirpath, filename)
			sigpath = os.path.join(dirpath, filename + SIG_EXTN)

			if filepath.endswith(SIG_EXTN):
				print 'Skipping signing of signature', filepath
				continue

			print 'Signing'
			print '  File:      %s' % filepath
			print '  Signature: %s' % sigpath

			args = [
				OPENSSL_PATH,
				'smime',
				'-sign',
				'-signer', cert_path,
				'-inkey', key_path,
				'-binary',
				'-in', filepath,
				'-outform', 'DER',
				'-out', sigpath
			]

			try:
				subprocess.check_call(args)
			except Exception as e:
				print 'Failed executing', args
				raise

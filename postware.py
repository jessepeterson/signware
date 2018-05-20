import munkilib.fetch
import munkilib.prefs
import munkilib.display
import tempfile
import os
import subprocess

OPENSSL_PATH='/usr/bin/openssl'
SIG_EXTN='.sig'

def process_post_fetch(url, path):
	manifestbaseurl = (munkilib.prefs.pref('ManifestURL') or
	                   munkilib.prefs.pref('SoftwareRepoURL') + '/manifests/')
	catalogbaseurl = (munkilib.prefs.pref('CatalogURL') or
	                  munkilib.prefs.pref('SoftwareRepoURL') + '/catalogs/')

	# the check for .sig here is to not loop forever as we recursively call
	# munkilib.fetch.munki_resource(). note this precludes legitimate
	# manifest and catalog names with ".sig" at the end of their names.
	if (not url.startswith(manifestbaseurl) and not url.startswith(catalogbaseurl)) or url.endswith('.sig'):
		return

	sigurl = url + SIG_EXTN
	osfile, sigpath = tempfile.mkstemp()
	os.close(osfile)

	munkilib.display.display_debug2('Fetching signature: %s to %s' % (sigurl, sigpath))

	try:
		munkilib.fetch.munki_resource(sigurl, sigpath)
	except Exception as e:
		munkilib.display.display_debug1('Problem fetching signature: %s' % str(e))
		# raise the error up to the caller to signify a problem fetching
		# (e.g. don't "trust" this manifest/catalog if no signature possible)
		raise

	# TODO: Instead of shelling out to OpenSSL the use Security framework via
	# ObjC using CMSDecoderSetDetachedContent, CMSDecoderCopySignerStatus,
	# et. al. to verify the signed status.
	args = [
		OPENSSL_PATH,
		'smime',
		'-verify',
		'-inform', 'DER',
		'-in', sigpath,
		'-content', path,
		'-out', '/dev/null',
	]

	# TODO: Whe/if we switch away from OpenSSL match our provided certificate
	# with something in th Keychain perhaps. This would make deployment of the
	# verification certificate easier as we can deploy it with a Profile, etc.
	cert_path = munkilib.prefs.pref('VerifyCMSCertPath')

	# TODO: Have a saner fallback than -noverify? Then this middleware fails
	# if a user doesn't configure a certificate at all. E.g. merely having
	# a valid CMS signature is 'valid' under the current code.
	args += ['-CAfile', cert_path] if cert_path else ['-noverify']

	try:
		# since this middleware is called in the middle of the fetch for the
		# catalogs/manifests, we cound as an error toward those downloads
		# if we raise an error. thus we effectively "fail" if our signature
		# is invalid.
		subprocess.check_call(args)
	finally:
		os.unlink(sigpath)


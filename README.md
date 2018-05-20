# signware - Validate CMS-signed manifests and catalogs in Munki

## Requirements

Munki needs to be patched to have support for "postware" (vs. "middlware") which allows for custom code to happen after a URL has been downloaded by `managedsoftwareupdate`. This is available in this PR:

https://github.com/munki/munki/pull/851

Why this method over, say, a Munki [preflight script](https://github.com/munki/munki/wiki/Preflight-And-Postflight-Scripts)? The main reason was to try and hook Munki in a way we could re-use Munki's middleware to fetch additional files (the signatures) where we need to be able to call Munki routines while its running (preflight/postflights are executed in another process). It's not clear that this couldn't simply use munki routine's as we do in the "postware" here, so I suppose its up for debate and certainly open to other methods.

## Using

### Generate certificates for use

Generate an X.509 Cert. And Key for use:

```
openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -sha256 -keyout cert.key -out cert.pem -subj "/CN=MunkiSigs"
```


### Use `signrepo` to sign your repository catalogs and manifests

After you've used `makecatalogs` as normal you need to sign your repository and generate the .sig files:

```
# the place where the manifests and catalogs directory is
$ cd /path/to/my/munki/repo

$ python /path/to/this/repo/signrepo.py /path/to/cert.pem /path/to/cert.key
Signing
  File:      manifests/testing
  Signature: manifests/testing.sig
Signing
  File:      catalogs/all
  Signature: catalogs/all.sig
Signing
  File:      catalogs/testing
  Signature: catalogs/testing.sig
```

### Configure the Munki client

* First, you need to be running the above patch version of Munki.
* Second you need to have the `postware.py` installed into Munki very similarly to how [Munki middleware](https://github.com/munki/munki/wiki/Middleware) is installed.
* Third you should install the signing certificate on the Munki client somewhere. This is used to verify the signatures from the Munki server. I.e. that nobody has tampered with the manifest or catalog files and configure it.
** Set the `VerifyCMSCertPath` Munki preference to where you installed the certificate: `sudo defaults write /Library/Preferences/ManagedInstalls.plist VerifyCMSCertPath /etc/munki_verify_cert.crt`.
* Once this is done Munki will now try to download the `.sig` files along with the manifests and catalogs and verifying them as they're received.

## FAQ

### Why are you only signing manifests and catalogs?

Pkginfos aren't touched by the Munki client at all. Packages themselves are already SHA256 cryptographically verified by Munki. This means as long as a catalog is signed and trusted, than any package defined with a hash signature is also trusted.

# nix-update-source

A simple tool for updating sources in nix derivations.

# Basic idea:

When you're writing a `src` attribute of a nix derivation, there are two types of attributes:

 - the ones you write
 - the ones the computer generates for you

In particular, you need the computer to generate the `sha256` digest in order to have a valid source. There are tools for this, nike `nix-prefetch-git` and `nix-prefetch-url`. But in order to use _those_, you need to translate the attributes you wrote into a command line, and (in the case of `fetchFromGitHub`) you also need to remember how to format a github archive URL given an author, repo and revision.

Computers are good at this stuff. Let's get them to do it for us.

# Usage on the command line (creating and updating source specifications):

```
cat src.in.json
{
  "type": "fetchFromGitHub",
  "repo": "piep",
  "owner": "timbertson",
  "rev": "version-0.8.0"
}
```

```
$ nix-update-source src.in.json --out src.json
```

What did it make?

```
$ cat src.json
{
  "fetch": {
    "args": {
      "owner": "timbertson",
      "repo": "piep",
      "rev": "version-0.8.0",
      "sha256": "1hz1lxd2s23vnjr37s2zn2lky9mhcxy1s3qdgsh8145dgnysdj3a"
    },
    "fn": "fetchFromGitHub"
  },
  "owner": "timbertson",
  "repo": "piep",
  "rev": "version-0.8.0",
  "type": "fetchFromGitHub"
}
```

It's a little repetitive, but it's got everything we might need. The `fetch` object tells us what function we're using, and `args` are the attributes we need to give it. The other toplevel keys are the information we gave to nix-update-source (you can use the output JSON as the input next time, if you'd rather not keep two JSON files).

### Tip 1: using substitutions:

We can get a bit fancier - let's ask the user for the `version` part of the tag, and put that in the `rev`:

```
cat src.in.json
{
  "type": "fetchFromGitHub",
  "repo": "piep",
  "owner": "timbertson",
  "rev": "version-{version}"
}
```

```
$ nix-update-source src.in.json --out src.json
/nix/store/pj2vwpfyfgj1k2i3mmnj0gax4nif2fx7-nix-update-source-0.4.0/bin/nix-update-source src.in.json --out src.json --prompt version
Loading src.in.json
Enter value for 'version': 0.8.0
# ...
$ cat src.json
{
  "fetch": {
    "args": {
      "owner": "timbertson",
      "repo": "piep",
      "rev": "version-0.8.0",
      "sha256": "1hz1lxd2s23vnjr37s2zn2lky9mhcxy1s3qdgsh8145dgnysdj3a"
    },
    "fn": "fetchFromGitHub",
    "rev": "version-0.8.0",
    "version": "0.8.0"
  },
  "owner": "timbertson",
  "repo": "piep",
  "rev": "version-{version}",
  "type": "fetchFromGitHub"
}
```

This is pretty handy - no need to modify the source specification on each release, just provide the latest version when you're updating it.

### Tip 2: `rev` doesn't have to be immutable:

If you don't make releases but simply build the latest commit on a branch, that's fine too - you can use `fetchgit` with a branch:

```
$ cat src.in.json
{
  "type": "fetchgit",
  "url": "git@github.com:timbertson/piep.git",
  "rev": "refs/heads/master"
}
```

(you need to use the full `refs/heads/master` format for branches, because `fetchgit` will assume `master` is a tag otherwise)


```
$ nix-update-source src.in.json --out src.json
$ cat src.json
{
  "fetch": {
    "args": {
      "fetchSubmodules": true,
      "rev": "93c3256c9b3c061109f831f391de7a7913211b58",
      "sha256": "10fg2h0zid1qq85ifr34k94qxn5ynr92m5hym6lnh6wzaf714q4i",
      "url": "git@github.com:timbertson/piep.git"
    },
    "fn": "fetchgit"
  },
  "rev": "refs/heads/master",
  "type": "fetchgit",
  "url": "git@github.com:timbertson/piep.git"
}
```

Note that while the input data was a branch, nix-update-source will pass the exact commit sha (and its corresponding sha256 digest) into fetchgit. So the derivation won't be checking out master, it'll repeatably be checking out this commit, which was the latest commit on `master` when you ran nix-update-source. Just run the same thing again when you want to update to a newer commit.

### Tip 3: you don't actually need a `src.in.json`

If you just want to script something and don't want to write a JSON file, you can just set attributes on the commandline:

```
$ nix-update-source --set type fetchFromGitHub --set repo piep --set owner timbertson --set rev version-0.8.0 --output src.json
```

# Usage in a nix derivation (using a source specification):

### NOTE: please don't use this in pulls requests to `nixpkgs`, you'll get yelled at. Keep reading below for the nixpkgs-friendly approach :)

The `nix-update-source` derivation in nixpkgs has a `fetch` function - you can use this at build time to import the source using this JSON file:

```
with (import <nixpkgs> {}):
let fetched = nix-update-source.fetch ./src.json; in
stdenv.mkDerivation {
  inherit (fetched) src version; # fetched has `src` as well as the input parameters (owner, repo, version, etc).
  # ...
}
```

# Usage in official nixpkgs

Unfortunately, the nixpkgs maintainers (well, some of them) don't like separating out generated data (the JSON output) from the manually written code (the derivation itself). So please don't go submitting packages which use `nix-update-source.fetch` into `nixpkgs` proper (I did it once, and it got reverted a week later). Instead, you can use nix-update-source to modify an existing derivation:

```
$ nix-update-source src.in.json --modify-nix default.nix
```

`defaut.nix` _should_ already be a derivation with a `src` attribute so that `nix-update-source` knows where to put the new information, but `src` doesn't need to be anything useful - `""` or `null` is fine. You'll get an error if it can't figure out what to replace.

You can play with `--nix-indent` and `--replace-attr` for additional control over what gets replaced (particularly handy for including a `version` attribute).

This is _not_ a proper parser for the nix language, but it should work for idiomatic, well-formatted derivations.



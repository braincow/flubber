# Flubber

Hi, I am Flubber. Your friendly time management utility and a companion for wonderful TailorDev/Watson time tracker. My purpose is not to replace Watson, but to bring those features you need most often to nice Gtk+ GUI and leave the power of Watson still available to you via its command line.

## Installation

To install me properly you need also a branched version of Watson as its still lacking a feature from upstream which has not been merged yet. So to install that first:

```
$ pip uninstall td-watson
$ git clone https://github.com/braincow/Watson.git
$ cd Watson
$ python setup.py install
```

After (uninstalling and) installing branched version of Watson you are ready to install Flubber:

```
$ git clone https://github.com/braincow/flubber.git
$ cd flubber
$ python setup.py install
```

## Usage

If installed system wide my .desktop file is also installed into /usr/share/applications and you can start me with your desktop environments application list. If I am not there however you can always execute me via "flubber" command from where setup.py installed my wrapper script (system wide default /usr/bin/)

## Support

Please open an issue to receive support and to suggest improvements.

## Contributing

Fork the project, create a new branch, make your changes, and submit a pull request.

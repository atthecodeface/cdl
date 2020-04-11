# CDL - cycle-based hardware design language

CDL is a language, compiler, and simulation harness (with Python
execution environment) for hardware design and generation, for
projects from the small to the enormous. The CDL tool suite is the
starting point for the Netronome NFP family of network processors,
which are multi-billion transistor devices.

## Installation

To get CDL, clone the github repo.

autoreconf --install --verbose

Then in another directory (potentially):

<cdl_src>/configure --prefix=<install_path>
make clean
make -j8 install

This will install:

<install_path>/bin/cdl
<install_path>/include/cdl/*h
<install_path>/lib/cdl/<some files>
<install_path>/lib/libcdl*
<install_path>/libexec/cdl/<some files>

## Installation with grip

First clone the grip.git repository

git clone https://github.com/atthecodeface/grip.git grip

Then clone cdl_tools_grip.git

git clone https://github.com/atthecodeface/cdl_tools_grip.git cdl_tools_grip

Then:

cd cdl_tools_grip
../grip/grip configure all
../grip/grip make configure
../grip/grip make install

This will clone all the required repositories for verilator, cdl, and
cross-compilers for RISC-V in the GNU toolchain, and build them.

then ../grip/grip shell

will provide a Bash shell with the path set to use these tools.

## Usage

The simples description is to follow some of the makefiles from the
regression suite; the design files are usually kept in cdl/src
directories, and a 'model_list' describes the hardware modules ready
for 'create_make' to build a makefile.

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

CDL has been around since the early 2000s, as a successor to numerous
simulation development tools. It grew out of a frustration with
Verilog and VHDL, which were (and are) very antiquated, and expensive
to simulate in large quantities.

## Credits

CDL has been written by Gavin Stark; along the way, particularly at
Netronome, there has been input from various folks as to what bits to
add, and patch proposals to get rid of warnings and the like -
particularly Jason McMullan and David Welch have provided good prods.

## License

CDL is released under a variety of licenses;

* The support library is put into the public domain - it is a set of
  useful functions that CDL uses throughout that do not want to
  encumber users in any fashion.

* The compiler is released under the GPL 2.0, so that patches and
  updates must be released in source form to help the community grow
  the tool.

* the simulation engine, which needs to be shippable with proprietary
code, is released under the LGPL.

Basically, see the license in the files...

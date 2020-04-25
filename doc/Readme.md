# CDL, simulation engine, etc

This repository contains the CDL design language compiler frontend,
backends for C++ and verilog, and a simulation engine that runs with the
C++ output, and the execution harnesses that allow for instantiation of
the simulation engine.

In addition there are scripts to enable description of complex
hardware designs, and regression test assistance.

All run with a support library.

## Support library

This is very antiquated, and is driven by the lack of support years
ago for decent C++ libraries. It provides some simple mechanisms for
various constructs (even simple lists) that in modern C++ coding
should be written with std::<> functions.

It also, though, supports the 'exec file' scripting language. "Yet
another scripting language", one might say - however, the purpose of
the language comes from being able to be deeply embedded in an
executable, in many instances, with the concept of time being driven
from the executable, not the scripting language (the language
interpreter, therefore, is the tail on the dog, not the dog).

## Simulation engine

The simulation engine is a C++ library that provides the framework for
cycle based simulation of hardware models.

The engine is instantiated, and then the models register themselves
with the engine; then a particular hardware design can be instantiated
using a set of these registered models (which in turn can have
submodules using registered models).

The simulation engine itself is independent of any scripting language.

The simulation engine includes basic models for SRAMs and a test
harness, which *does* use a scripting language (to supply the test).

## Execution harnesses

To enable the simulation engine to be invoked as a batch simulator, a
batch-mode 'execution harness' is provided; this takes an exec file
script which defines what hardware description to load, when to reset
it, what signals to generate VCD files for, and how long to simulate
for. The hardware description that it loads is also an exec file
(note, nested interpreters...) which describes the top level modules,
any options they require, and their toplevel wiring. Frequently this
will be just instantiating a testbench model and assigning clocks and
reset. The execution harness links with the simulation engine and
hardware models to provide the batch simulator.

A second execution harness is provided which is a python C model; this
exposes the hardware description functions as Python methods of a
'simulation engine library', which a Python program can then use to
define the toplevel hardware and options for it. Some of the options,
for example for testbenches, may be execution scripts - which in turn
can be Python class instances (subclassed from the simulation engine
exec file class). Hence a complete Python-based test environment is
provided. The execution harness and simulation engine combined are
linked with the hardware models to produce a dynamic library that
Python can import.

## CDL language front-end

CDL is a synthesizable hardware design language with a C-like syntax.
It describes hardware modules (like Verilog and SystemVerilog), with a
refinement that clocks are fundamentally separate for input and output
signals (as they are in silicon and FPGA design).

The CDL front-end creates a model description (in a sense an IR -
*intermediate representation*) that backends can target at Verilog or
C++ (or, indeed, other output forms).

CDL version 1.4 has been used for design of commercial multi-billion
transistor silicon designs.

## CDL language back-ends

The backends for CDL are C++ models, which can be compiled and used
with the simulation engine, and Verilog, which can be used for
Verilator, FPGAs or silicon design.

In addition there is an XML output which provides for analysis of the
structure of a (or many) module.

The Verilog demands of Verilator, FPGAs and silicon design differ
slightly (FPGAs cannot cope with gated clocks, silicon requires test
insertion, etc) and the backends provide appropriate settings.

A new backend in CDL 2.0 allows generation of a C++ model wrapper for
a Verilated C++ model of that module. This sounds complicated, but it
is not really. Consider a module *fred* that is stable, and whose
verilog is most under test; module *fred* can have its verilog
generated, and for any submodules of *fred* too. This verilog can, of
course, be compiled with Verilator to create a C++ model. Now,
verilator C++ models are much faster to execute than CDL C++ models,
which themselves provide for much greater visibility and so on. So
there is now a *fred* verilator C++ compiled library, with a toplevel
C++ class called *Vfred*. The C++ model wrapper backend creates a new
CDL simulation model called (by default) *cv__fred*, which is identical in ports
etc to the CDL simulation model *fred*, and is a drop-in replacement;
*cv_fred* uses an instance of *Vfred*, and so should execute faster
than the pure CDL C model.

CDL models of memories are internal CDL constructs (instances of
se_sram*); Verilator models have to have Verilog versions of these,
and verilog does not provide for dynamic interaction with the
memories - unlike CDL, that has a messaging interface during
simulation to all modules. So a CDL design can, at run time, load an
SRAM with the contents of a MIF file; Verilator designs cannot. (This
is one of many of the features one loses going from CDL to Verilog -
there are downsides to the speed increases). CDL provides verilog code
for the se_sram* modules, which have a "/*verilator public*/" marking
on the ram memory instances; this makes Verilator produce somewhat
slower modules, but they expose the ram memories so that the C++ model
wrapper can support loading and resetting of the memories in the same
manner as se_sram* CDL models do. In theory any "/*verilator public*/"
marked element in the verilog can be exposed to CDL, for example for
waveforms, but this is not yet implemented.

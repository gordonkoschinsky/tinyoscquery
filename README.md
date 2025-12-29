# python-oscquery

An OSCQuery library for python.

![Python Version >=3.10](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fgordonkoschinsky%2Fpython-oscquery%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)
![Tests](https://github.com/gordonkoschinsky/python-oscquery/actions/workflows/python-package.yml/badge.svg)

[OSCQuery](https://github.com/Vidvox/OSCQueryProposal) is a protocol that allows
an [Open Sound Control (OSC)](https://opensoundcontrol.stanford.edu) server to
announce its presence and capabilities over the network.
Clients can discover the server via [zeroconf](https://en.wikipedia.org/wiki/Zero-configuration_networking) and query
the address space via HTTP.

This library provides an integration with  [python-osc](https://pypi.org/project/python-osc/).
The namespace that is configured to be announced via the OSCQuery server is also used to automatically
type-check incoming OSC messages. For this purpose, a wrapper around a python-osc handler callback function
is provided.

## Status

### Server

The [core functionality](https://github.com/Vidvox/OSCQueryProposal?tab=readme-ov-file#core-functionality) (according to
the specification) is implemented.
Some [optional attributes](https://github.com/Vidvox/OSCQueryProposal?tab=readme-ov-file#optional-attributes) like
ACCESS, VALUE and DESCRIPTION are also implemented. However, lists (or other python
iterables) are not supported as value types.

Completely missing is
the [websocket communication](https://github.com/Vidvox/OSCQueryProposal?tab=readme-ov-file#optional-bi-directional-communication).
So no "listening" is possible.

### Client / Browser

Discovery of other OSCQuery servers on the network and querying of the OSC address space is implemented.

## Installation

To be written.

## Usage

### Configuring the OSC address space

To be written. See the example files for now.

### Advertising an OSCQuery Service

To be written. See the example files for now.

### Discovering and Querying other OSCQuery Services

To be written. See the example files for now.

## Project To-Do

- [ ] Build a package and publish on PyPi
- [ ] Add more tests
- [ ] Add a mechanism to update OSC nodes with new values
- [ ] Add the RANGE attribute and validate messages against it
- [ ] Add websocket communication as per spec
- [ ] Add more documentation
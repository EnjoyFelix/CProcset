# C-ProcSet

This project is a C implementation of the ProcSet data structure, originally implemented in Python. The goal is to improve the performance of the program while maintaining the Python interface. The implementation is based on cPython and utilizes the Python.h header file.

## Features

-   **ProcSet Creation**: Create a ProcSet object to represent a set of intervals.
-   **ProcSet Deletion**: Delete a ProcSet object and free the associated memory.
-   **String Representation (repr)**: Generate a string representation of a ProcSet object.
-   **String Conversion (str)**: Convert a ProcSet object to a human-readable string format.
-   **Union**: Perform the union operation on two ProcSet objects, creating a new ProcSet that contains all the intervals from both sets.
-   **Intersection**: Perform the intersection operation on two ProcSet objects, creating a new ProcSet that contains only the intervals common to both sets.
-   **Difference**: Perform the difference operation on two ProcSet objects, creating a new ProcSet that contains the intervals from the first set that are not present in the second set.
-   **Symmetric Difference**: Perform the symmetric difference operation on two ProcSet objects, creating a new ProcSet that contains the intervals that are present in either of the sets, but not in both.

## Getting Started

To use the C implemenation of `ProcSet` in your project, follow the steps below:

### Prerequisites

Before installing the `procset` module, ensure that you have the following prerequisites:

-   Python development headers and libraries (e.g., python3-dev)
-   C compiler (e.g., GCC or Clang), based on C99
-   Python setuptools package (if not already installed)

The specific versions of these prerequisites may vary depending on your system. Make sure you have the minimum required versions to successfully build and install the `procset` module.

### Installation

To install the `procset` module, follow these steps:

1. Clone the repository: 
``` bash
git clone https://gitlab.inria.fr/ctrl-a/internships/2023_procset/c-procset
``` 

2. Navigate to the project directory:
```bash 
cd c-procset
```

3. Run the installation command:
```bash
python setup.py install
``` 
This command will invoke the `setup.py` script, which handles the building and installation process.
Note: Depending on your system configuration, you may need to use `python3` instead of `python` if you have both Python 2 and Python 3 installed. 

4. Once the installation is complete, you can start using the `procset` module in your Python programs.
```python
import procset
``` 
    
Ensure that you have the necessary permissions to install Python packages globally on your system. Alternatively, you can create a virtual environment and perform the installation within that environment.
    

By following these steps, you should be able to successfully install and use the `procset` module in your Python environment.

## Usage

Here is an example of how to use the C-ProcSet library in your Python program:

```python
import procset

# Create ProcSet objects
proc1 = procset.ProcSet("11-45 88-100")
proc2 = procset.ProcSet("33-54 63-74 79-94")

# Perform operations on the ProcSet objects
proc_union = proc1.union(proc2)
proc_intersection = proc1.intersection(proc2)
proc_difference = proc1.difference(proc2)
proc_symmetric_diff = proc1.symmetric_difference(proc2)

# Display the string representation of ProcSet objects
print(f"proc1 with repr: {repr(proc1)}")
print(f"proc2 with str : {proc2}")


# Display the results of the operations
print(f"union : {proc_union}")
print(f"intersection : {proc_intersection}")
print(f"difference : {proc_difference}")
print(f"symmetric-difference : {proc_symmetric_diff}")

# Create and display an empty ProcSet
proc_empty = procset.ProcSet()
print(f"empty : {proc_empty}")
```
### Output
```bash
proc1 with repr: ProcSet(11-45 88-100)
proc2 with str : 33-54 63-74 79-94
union : 11-54 63-74 79-100
intersection : 33-45 88-94
difference : 11-32 95-100
symmetric-difference : 11-32 46-54 63-74 79-87 95-100
empty : 
```
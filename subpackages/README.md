Subpackages
===========

Here are placed tasks which needs extra dependencies that cannot be placed into the RKD core.

**Examples:**
- Tasks that requires dependencies that are written in C, and compiled with gcc/g++ when installing
- Tasks pulling too many dependencies


Normally we would place such python modules in a separate repository, but we see a value of having exactly those tasks together with RKD in one repository.

**Advantages of single repository:**
- Single versioning and compatibility between RKD, standardlib and subpackages
- Less to maintain
- Guaranteed integrity

# Call the shared library from Julia
ccall((:main, "build/main.so"), Cvoid, ())

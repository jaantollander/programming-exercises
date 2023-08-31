module MultipleDispatch

export A, A1, A2, f

# Abstract type
abstract type A end

# Concrete types
struct A1 <: A end
struct A2 <: A end

# Methods
## One argument (single dispatch)
f(::Type{A1}) = "A1"
f(::Type{A2}) = "A2"

## Two or more arguments (multiple dispatch)
## Two arguments
f(a1::Type{<:A}, a2::Type{<:A}) = f(a1) * "×" * f(a2)

## Variable number of arguments
f(a::Type{<:A}...) = join(f.(a), "×")

end


# Lets import the module
using .MultipleDispatch

# Single dispatch
f(A1)
f(A2)

# Multiple dispatch
f(A1, A1)
f(A1, A2)
f(A2, A1)
f(A2, A2)

# We can extend new concrete types dynamically
struct A3 <: A end
MultipleDispatch.f(::Type{A3}) = "A3"
f(A1, A2, A3)

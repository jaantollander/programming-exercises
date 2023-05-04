x = collect(Cint, 1:5)
println(x)
res = ccall((:vectorMean, "build/mean.so"), Float64, (Ptr{Cint},Cint), x, 5)
println(res)

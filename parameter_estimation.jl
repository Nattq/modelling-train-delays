using Evolutionary
using Statistics
using Random

function rungekutta4(f::Function, x::LinRange, initial_condition::Vector, params::Vector = [])::Tuple{LinRange, Array}
    n = length(x) - 1
    solution = Array{Float64}(undef, n+1, length(initial_condition))
    solution[1, :] =  initial_condition
    h = x[2] - x[1]  
    for i in 1:n
        k₀ = h * f(solution[i, :], params...)
        k₁ = h * f(solution[i, :] + 0.5 * k₀, params...)
        k₂ = h * f(solution[i, :] + 0.5 * k₁, params...)
        k₃ = h * f(solution[i, :] + k₂, params...)
        solution[i+1, :] = solution[i, :] + (k₀ + 2*(k₁ + k₂) + k₃) / 6
    end
    x, solution
end

function SIR_derivatives(SIR_numbers::Vector{Float64}, β::Number, γ::Number)::Vector{Float64}
    S, I, R = SIR_numbers
    N = sum(SIR_numbers)
    dS = -β*S*I/N  
    dI = β*S*I/N - γ*I  
    dR = γ*I  
    [dS, dI, dR]
end

function mean_relative_error(xs::Vector{Float64}, ys::Vector{Float64})::Number 
    mean(abs.(xs .- ys)./xs)
end

function fitness_func(solution)
    _, s = rungekutta4(SIR_derivatives, LinRange(0.0, 109.0, 1091), [235.0, 14.0, 0.0], solution)
    I_m = s[:, 2]
    mean_relative_error(I, I_m)
end

β = 0.2 
γ = 0.1
x, data = rungekutta4(SIR_derivatives, LinRange(0.0, 109.0, 1091), [235.0, 14.0, 0.0], [β, γ])
I = data[:, 2]

Evolutionary.optimize(
    fitness_func, 
    BoxConstraints([0.0, 0.0], [1.0, 1.0]),
    rand(2),
    GA(populationSize = 100, selection = susinv, crossover = AX, mutation = uniform(0.1), mutationRate = 0.5, ε = 0.1)
)
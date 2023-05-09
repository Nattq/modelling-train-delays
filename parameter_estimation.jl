using Evolutionary
using Statistics
using Random
using XLSX
using DataFrames

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

function mean_relative_error(xs, ys)::Number 
    mean(abs.(xs .- ys)./xs)
end

function fitness_func(solution, T, S₀, I₀, I)
    _, s = rungekutta4(SIR_derivatives, LinRange(0.0, T, 10T+1), [S₀, I₀, 0.0], solution)
    I_m = s[:, 2]
    mean_relative_error(I, I_m)
end

df = DataFrame(XLSX.readtable("data//df_AC_zgrupowane.xlsx", "Sheet1"))
df[:, "beta"] = Vector{Float64}(undef, nrow(df))
df[:, "gamma"] = Vector{Float64}(undef, nrow(df))
df[:, "błąd_dopasowania"] = Vector{Float64}(undef, nrow(df))

for (row_number, row) in enumerate(eachrow(df))
    I₀ = row["czy_opoznienie_wyjazd"]
    Iₜ = row["czy_opoznienie_przyjazd"]
    S₀ = row["nazwa_pociagu"] - I₀
    T = row["czas_przejazdu_super_krawedz"]
    I = (Iₜ - I₀)/T .* LinRange(0.0, T, 10T+1) .+ I₀
    if I₀ != Iₜ
        println(row_number) #TEST
        solution = Evolutionary.optimize(
            x -> fitness_func(x, T, S₀, I₀, I), 
            BoxConstraints([0.0, 0.0], [1.0, 1.0]),
            rand(2),
            GA(populationSize = 100, selection = susinv, crossover = AX, mutation = uniform(0.1), mutationRate = 0.5, ε = 0.1)
        )
        df[row_number, "beta"] = solution.minimizer[1]
        df[row_number, "gamma"] = solution.minimizer[2]
        df[row_number, "błąd_dopasowania"] = solution.minimum
    end
end

XLSX.writetable("data/parametry.xlsx", df)

import numpy as np

def curvatura_max_muestreo(v_i, v_j, s_i, s_j, q, EI, L):
    # version actual (rev01): 401 puntos
    xi = np.linspace(0.0, 1.0, 401)
    x = xi * L
    vpp = ((-6.0 + 12.0 * xi) * v_i + (6.0 - 12.0 * xi) * v_j) / L ** 2 \
        + s_i * (-4.0 + 6.0 * xi) / L + s_j * (-2.0 + 6.0 * xi) / L \
        + q * (12.0 * x ** 2 - 12.0 * L * x + 2.0 * L ** 2) / (24.0 * EI)
    return float(np.max(np.abs(EI * vpp)))

def curvatura_max_exacta(v_i, v_j, s_i, s_j, q, EI, L):
    """Maximo |M| = EI * v'' en 0 <= x <= L (Euler-Bernoulli exacto entre extremos).
    v'' es un polinomio de grado 2 en x: M(x) = A0 + A1*x + A2*x**2. El maximo de |M| en un
    intervalo cerrado esta en un extremo del intervalo o en el vertice de la parabola."""
    A0 = EI * (-6.0 * v_i / L**2 + 6.0 * v_j / L**2 - 4.0 * s_i / L - 2.0 * s_j / L + q * L**2 / (12.0 * EI))
    A1 = EI * (12.0 * v_i / L**3 - 12.0 * v_j / L**3 + 6.0 * s_i / L**2 + 6.0 * s_j / L**2 - q * L / (2.0 * EI))
    A2 = EI * (q / (2.0 * EI))
    M = lambda x: A0 + A1 * x + A2 * x * x
    candidatos = [0.0, L]
    if A2 != 0.0:
        xv = -A1 / (2.0 * A2)
        if 0.0 < xv < L:
            candidatos.append(xv)
    return float(max(abs(M(x)) for x in candidatos))

if __name__ == '__main__':
    rng = np.random.default_rng(7)
    peor_rel = 0.0; n_menor = 0
    for _ in range(3000):
        L = rng.uniform(50, 800)
        vi, vj = rng.normal(0, 0.5, 2); si, sj = rng.normal(0, 0.01, 2)
        q = rng.normal(0, 0.3); EI = rng.uniform(1e5, 1e8)
        a = curvatura_max_muestreo(vi, vj, si, sj, q, EI, L)
        b = curvatura_max_exacta(vi, vj, si, sj, q, EI, L)
        if b < a - 1e-9 * max(1, abs(b)): n_menor += 1
        peor_rel = max(peor_rel, abs(a - b) / max(1e-12, abs(b)))
    print('casos con exacta < muestreo (error): ', n_menor)
    print('error relativo maximo del muestreo de 401 puntos:', f'{peor_rel:.3e}')
    L = 600.0; q = 0.2; EI = 2.04e6 * 2000.0
    si = q*L**3/(24*EI); sj = -q*L**3/(24*EI)  # pendientes de extremo de la viga simple (M = 0 en ambos apoyos)
    print('viga SS uniforme: exacta =', curvatura_max_exacta(0, 0, si, sj, q, EI, L), '| muestreo =', curvatura_max_muestreo(0, 0, si, sj, q, EI, L), '| esperado qL^2/8 =', q*L**2/8)
    print('sin carga, extremos desplazados: exacta', curvatura_max_exacta(0.0, 1.0, 0.0, 0.0, 0.0, EI, L), 'muestreo', curvatura_max_muestreo(0.0, 1.0, 0.0, 0.0, 0.0, EI, L))

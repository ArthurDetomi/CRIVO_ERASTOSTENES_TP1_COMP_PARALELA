# Crivo de Eratóstenes — Implementação Sequencial e Paralela com MPI

**A documentação se encontra em docs/TP1_COMP_PARALELA.pdf**

Este projeto implementa o **Crivo de Eratóstenes** em duas versões:

- **Sequencial** (`linear/`): implementação clássica em C.
- **Paralela** (`paralelo/`): implementação com MPI, seguindo o modelo mestre-escravo.

Além disso, o projeto inclui um _script_ Python (`benchmark.py`) que automatiza a compilação, execução e coleta de métricas (tempo, _speedup_ e eficiência paralela), gerando gráficos comparativos.

---

## 1. Estrutura do Projeto

```

.
├── benchmark.py # Script Python de benchmark e geração de gráficos
├── comparacao_tempos.png # Gráfico gerado pelo benchmark
├── eficiencia.png # Gráfico gerado pelo benchmark
├── speedup.png # Gráfico gerado pelo benchmark
├── requirements.txt # Dependências Python
├── resultados.csv # Resultados das execuções (gerado)
├── testes.csv # Configuração dos testes (entrada do benchmark)
├── docs/ # Documentação
├── examples/ # Exemplos auxiliares de MPI (reduce, scatter)
│ ├── example_reduce.c
│ └── example_scatter.c
├── linear/ # Versão sequencial
│ ├── include/
│ │ └── tempo.h
│ ├── Makefile
│ ├── obj/
│ ├── output/
│ └── src/
│ ├── crivo_linear.c
│ └── tempo.c
└── paralelo/ # Versão paralela com MPI
├── include/
│ └── tempo.h
├── Makefile
├── obj/
├── output/
└── src/
└── crivo_paralelo.c

```

---

## 2. Requisitos

Antes de executar o projeto, certifique-se de que os seguintes programas estão instalados:

### 2.1. Compilador C e bibliotecas

- **GCC** (ou outro compilador C compatível)
- **Open MPI** (fornece `mpicc` e `mpirun`)

Verifique se o MPI está instalado corretamente:

```bash
mpicc --version
mpirun --version
```

### 2.2. Python (para o benchmark)

- **Python 3.8+**
- Bibliotecas listadas em `requirements.txt` (principalmente `matplotlib`)

Instalação das dependências:

```bash
pip install -r requirements.txt
```

---

## 3. Compilação

Cada versão possui seu próprio `Makefile`. A partir da raiz do projeto:

### 3.1. Compilar a versão sequencial

```bash
cd linear
make
```

O binário será gerado como `linear/crivo_linear`.

Para limpar os arquivos objeto e o binário:

```bash
make clean
```

### 3.2. Compilar a versão paralela

```bash
cd paralelo
make
```

O binário será gerado como `paralelo/crivo_paralelo`.

Para limpar:

```bash
make clean
```

> **Observação:** o `Makefile` da versão paralela deve usar `mpicc` em vez de `gcc`.

---

## 4. Execução

### 4.1. Versão sequencial

A partir do diretório `linear/`:

```bash
cd linear
./crivo_linear <N>
```

**Exemplo** — encontrar todos os primos até 1.000.000:

```bash
./crivo_linear 1000000
```

**Saída esperada:**

- Impressão no terminal:
  ```
  Tempo total de execução:
  Tempo Real: 0.00512345 segundos
  ```
- Arquivo `output/saida_linear.txt` contendo um primo por linha, em ordem crescente.

### 4.2. Versão paralela com MPI

A partir do diretório `paralelo/`:

```bash
cd paralelo
mpirun -n <P> ./crivo_paralelo <N>
```

Onde:

- `<P>` é o número de processos MPI (ex.: `2`, `4`, `8`).
- `<N>` é o limite superior do crivo.

**Exemplo** — com 4 processos e N = 10.000.000:

```bash
mpirun -n 4 ./crivo_paralelo 10000000
```

**Saída esperada:**

- Cada processo imprime a faixa que está processando:
  ```
  Rank 0: Responsavel pelo intervalo [2, 2500000]
  Rank 1: Responsavel pelo intervalo [2500001, 5000000]
  ...
  ```
- Ao final, o processo mestre imprime:
  ```
  Tempo paralelo: 0.01467529 segundos
  ```
- Arquivo `output/saida_paralelo.txt` com os primos em ordem crescente.

---

## 5. Benchmark automatizado

O script `benchmark.py` compila as duas versões, executa os testes definidos em `testes.csv`, coleta os tempos e gera:

- `resultados.csv` com tempos, _speedup_ e eficiência;
- `comparacao_tempos.png`;
- `speedup.png`;
- `eficiencia.png`.

### 5.1. Configurar os testes

Edite `testes.csv` com o seguinte formato:

```csv
Entradas,N processos
10000,2
10000,4
10000,8
10000000,2
10000000,4
10000000,8
100000000,2
100000000,4
100000000,8
```

- **`Entradas`**: valor de \(N\). Se deixado em branco, o script reutiliza o último \(N\) informado.
- **`N processos`**: quantidade de processos MPI.

### 5.2. Executar

Na raiz do projeto:

```bash
python3 benchmark.py
```

**O que o script faz:**

1. Compila `linear/` e `paralelo/` via `make`.
2. Para cada \(N\) distinto, executa a versão sequencial **uma única vez**.
3. Para cada combinação \((N, P)\), executa a versão paralela **5 vezes** (constante `REPETICOES_PARALELO`) e usa a **mediana** como tempo representativo.
4. Calcula _speedup_ e eficiência:
   \[
   S(p) = \frac{T(1)}{T(p)}, \qquad E(\%) = 100 \cdot \frac{S(p)}{p}
   \]
5. Salva os resultados em `resultados.csv` e gera os três gráficos.

### 5.3. Ajustar o número de repetições

No topo de `benchmark.py`:

```python
REPETICOES_PARALELO = 5
```

Aumente esse valor para reduzir o ruído experimental, ou diminua para testes mais rápidos.

---

## 6. Arquivos de saída

| Arquivo                              | Descrição                                             |
| ------------------------------------ | ----------------------------------------------------- |
| `linear/output/saida_linear.txt`     | Primos encontrados pela versão sequencial.            |
| `paralelo/output/saida_paralelo.txt` | Primos encontrados pela versão paralela.              |
| `resultados.csv`                     | Tabela com tempos, _speedup_ e eficiência.            |
| `comparacao_tempos.png`              | Gráfico de tempos (escala logarítmica).               |
| `speedup.png`                        | Gráfico de _speedup_ com linha de referência \(S=1\). |
| `eficiencia.png`                     | Gráfico de eficiência com linha de 100%.              |

---

## 7. Exemplos rápidos

**Verificar se os primos até 100 estão corretos (versão sequencial):**

```bash
cd linear
./crivo_linear 100
cat output/saida_linear.txt
```

**Comparar sequencial e paralelo para N = 1.000.000:**

```bash
# Sequencial
cd linear && ./crivo_linear 1000000

# Paralelo com 4 processos
cd ../paralelo && mpirun -n 4 ./crivo_paralelo 1000000
```

**Rodar o benchmark completo:**

```bash
python3 benchmark.py
```

---

## 8. Notas sobre desempenho

- Para \(N\) pequeno (ex.: 10.000), a versão paralela tende a ser **mais lenta** que a sequencial, pois os custos de inicialização e comunicação do MPI dominam o tempo total.
- Para \(N\) grande (ex.: 10.000.000 ou mais), a paralelização passa a compensar, com _speedup_ crescente até certo número de processos.
- O `MPI_Gatherv` concentra todos os resultados no processo mestre (rank 0), o que pode se tornar um gargalo para \(N\) muito grande.
- Não foi utilizada a ferramenta `gprof` neste trabalho; a análise baseia-se nos tempos totais medidos pelo `benchmark.py`.

---

## 9. Limpeza

Para remover binários, objetos e arquivos gerados:

```bash
cd linear && make clean
cd ../paralelo && make clean
rm -f resultados.csv comparacao_tempos.png speedup.png eficiencia.png
```

---

## 10. Referências

- Crivo de Eratóstenes — Wikipédia: https://pt.wikipedia.org/wiki/Crivo_de_Eratóstenes
- Khan Academy — Crivo de Eratóstenes: https://www.youtube.com/watch?v=vJg3unB0J7A
- Open MPI Documentation: https://www.open-mpi.org/doc/

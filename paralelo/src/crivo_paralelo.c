#include <math.h>
#include <mpi/mpi.h>
#include <stdio.h>
#include <stdlib.h>

void crivo_paralelo(char *primos_local, char *primos_base, int inicio, int fim,
                    int limite) {
  for (int p = 2; p <= limite; p++) {
    if (primos_base[p]) {

      long long primeiro_multiplo = (long long)p * p;

      if (primeiro_multiplo < inicio) {
        int resto = inicio % p;

        if (resto == 0) {
          primeiro_multiplo = inicio;
        } else {
          primeiro_multiplo = inicio + (p - resto);
        }
      }

      for (long long multiplo = primeiro_multiplo; multiplo <= fim;
           multiplo += p) {
        primos_local[multiplo - inicio] = 0;
      }
    }
  }
}

void liberar_memoria(void **array) {
  free(*array);
  *array = NULL;
}

int main(int argc, char **argv) {
  MPI_Init(&argc, &argv);

  int size, rank;

  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  if (argc != 2) {
    if (rank == 0) {
      fprintf(stderr, "Uso: %s <N>\n", argv[0]);
    }

    MPI_Finalize();
    return 1;
  }

  int n = atoi(argv[1]);

  if (rank == 0)
    printf("N = %d\n", n);

  int quantidade = n - 1;

  int lens[size], disps[size];

  for (int i = 0; i < size; i++) {
    lens[i] = quantidade / size;
    disps[i] = 0;
  }

  int resto = quantidade % size;

  int aux = 0;
  for (int i = 0; i < resto; i++) {
    if (aux >= size) {
      aux = 0;
    }
    lens[aux]++;
    aux++;
  }

  disps[0] = 0;

  for (int i = 1; i < size; i++) {
    disps[i] = disps[i - 1] + lens[i - 1];
  }

  int tamanho_local = lens[rank];

  int inicio = 2 + disps[rank];
  int fim = inicio + tamanho_local - 1;

  printf("Rank %d: Responsavel pelo intervalo [%d, %d]\n", rank, inicio, fim);

  char *primos_local = (char *)malloc(tamanho_local);

  for (int i = 0; i < tamanho_local; i++) {
    primos_local[i] = 1;
  }

  int limite = (int)sqrt(n);

  char *primos_base = malloc(limite + 1);

  MPI_Barrier(MPI_COMM_WORLD);

  double tempo_inicio = MPI_Wtime();

  if (rank == 0) {
    for (int i = 0; i <= limite; i++) {
      primos_base[i] = 1;
    }

    primos_base[0] = 0;
    primos_base[1] = 0;

    for (int p = 2; p * p <= limite; p++) {
      if (primos_base[p]) {
        for (int multiplo = p * p; multiplo <= limite; multiplo += p) {
          primos_base[multiplo] = 0;
        }
      }
    }
  }

  MPI_Bcast(primos_base, limite + 1, MPI_CHAR, 0, MPI_COMM_WORLD);

  crivo_paralelo(primos_local, primos_base, inicio, fim, limite);

  char *primos_final = NULL;

  if (rank == 0) {
    primos_final = malloc(quantidade);
  }

  MPI_Gatherv(primos_local, lens[rank], MPI_CHAR, primos_final, lens, disps,
              MPI_CHAR, 0, MPI_COMM_WORLD);

  double tempo_fim = MPI_Wtime();
  double tempo_local = tempo_fim - tempo_inicio;
  double tempo_maximo = 0.0;

  MPI_Reduce(&tempo_local, &tempo_maximo, 1, MPI_DOUBLE, MPI_MAX, 0,
             MPI_COMM_WORLD);

  if (rank == 0) {
    printf("Tempo paralelo: %.8f segundos\n", tempo_maximo);
  }

  if (rank == 0) {
    FILE *arq_saida = fopen("output/saida_paralelo.txt", "w");

    if (arq_saida == NULL) {
      perror("Erro ao gravar arquivo");

      liberar_memoria((void **)&primos_local);
      liberar_memoria((void **)&primos_base);
      liberar_memoria((void **)&primos_final);

      MPI_Finalize();

      return 1;
    }

    for (int i = 0; i < quantidade; i++) {

      if (primos_final[i]) {
        fprintf(arq_saida, "%d\n", i + 2);
      }
    }

    fclose(arq_saida);
  }

  liberar_memoria((void **)&primos_local);
  liberar_memoria((void **)&primos_base);
  liberar_memoria((void **)&primos_final);

  MPI_Finalize();

  return 0;
}
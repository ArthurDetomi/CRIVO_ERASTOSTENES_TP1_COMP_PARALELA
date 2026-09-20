#include <mpi/mpi.h>
#include <stdio.h>
#include <stdlib.h>

double scalar_prod(double *v1, double *v2, int n) {
  double result = 0;
  for (int i = 0; i < n; i++) {
    result += v1[i] * v2[i];
  }
  return result;
}

int main(int argc, char **argv) {
  MPI_Init(&argc, &argv);

  // size numero de processadores, rank qual processo
  int rank, size;

  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  int n = 100000;
  double *vector1, *vector2;

  if (n % size != 0) {
    printf("n (%d) nao eh divisivel por size (%d)\n", n, size);
  } else {

    int vec_size = n / size;
    double partial = 0;

    if (rank == 0) {

      vector1 = (double *)malloc(sizeof(double) * n);
      vector2 = (double *)malloc(sizeof(double) * n);

      for (int i = 0; i < n; i++) {
        vector1[i] = i + 1;
        vector2[i] = i + 1;
      }

      for (int i = 1; i < size; i++) {
        // Pular o pedaço de cada um para dividir uma parte do vetor para cada
        // processo
        MPI_Send(vector1 + i * vec_size, vec_size, MPI_DOUBLE, i, 999,
                 MPI_COMM_WORLD);
        MPI_Send(vector2 + i * vec_size, vec_size, MPI_DOUBLE, i, 999,
                 MPI_COMM_WORLD);
      }

      partial = scalar_prod(vector1, vector2, vec_size);
      printf("Partial Scalar prod = %lf\n", partial);

    } else {

      vector1 = (double *)malloc(sizeof(double) * vec_size);
      vector2 = (double *)malloc(sizeof(double) * vec_size);
      MPI_Status st;
      MPI_Recv(vector1, vec_size, MPI_DOUBLE, 0, 999, MPI_COMM_WORLD, &st);
      MPI_Recv(vector2, vec_size, MPI_DOUBLE, 0, 999, MPI_COMM_WORLD, &st);

      partial = scalar_prod(vector1, vector2, vec_size);
      printf("Partial scalar = %lf\n", partial);
    }
    double final;
    MPI_Reduce(&partial, &final, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0)
      printf("Final scalar prod= %lf\n", final);
  }

  MPI_Finalize();
}
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

  int n = 6;
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
    } else {
      vector1 = (double *)malloc(sizeof(double) * vec_size);
      vector2 = (double *)malloc(sizeof(double) * vec_size);
    }

    MPI_Scatter(vector1, vec_size, MPI_DOUBLE, vector1, vec_size, MPI_DOUBLE, 0,
                MPI_COMM_WORLD);
    MPI_Scatter(vector2, vec_size, MPI_DOUBLE, vector2, vec_size, MPI_DOUBLE, 0,
                MPI_COMM_WORLD);

    partial = scalar_prod(vector1, vector2, vec_size);
    printf("Partial scalar prod = %lf\n", partial);
    double final;
    MPI_Reduce(&partial, &final, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0)
      printf("Final scalar prod= %lf\n", final);
  }

  MPI_Finalize();
}
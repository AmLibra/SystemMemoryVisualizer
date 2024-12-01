#include <stdlib.h>
#include <stdio.h>
#include <time.h>

int main() {
    srand(time(NULL));
    int *array = NULL;
    size_t size = 1024;  // Start with a small size

    for (int i = 0; i < 100; i++) {
        array = (int *)realloc(array, size * sizeof(int));
        if (array == NULL) {
            perror("Failed to allocate memory");
            exit(EXIT_FAILURE);
        }

        for (size_t j = 0; j < size; j++) {
            array[j] = rand();  // Populate with random numbers
        }

        printf("Reallocated to %zu integers\n", size);
        size *= 2;  // Double the size
    }

    free(array);
    return 0;
}

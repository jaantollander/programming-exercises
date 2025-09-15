#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_FILENAME_LENGTH 256
#define BUFFER_SIZE 1024

void printUsage() {
    printf("Usage: program_name --input <input_file_path> --output <output_file_path>\n");
}

int main(int argc, char *argv[]) {
    char inputFile[MAX_FILENAME_LENGTH];
    char outputFile[MAX_FILENAME_LENGTH];
    FILE *input, *output;
    char buffer[BUFFER_SIZE];
    size_t bytesRead;

    if (argc != 5 || strcmp(argv[1], "--input") != 0 || strcmp(argv[3], "--output") != 0) {
        printUsage();
        return EXIT_FAILURE;
    }

    strcpy(inputFile, argv[2]);
    strcpy(outputFile, argv[4]);

    input = fopen(inputFile, "r");
    if (input == NULL) {
        printf("Error: Unable to open input file '%s'\n", inputFile);
        return EXIT_FAILURE;
    }

    output = fopen(outputFile, "w");
    if (output == NULL) {
        printf("Error: Unable to open output file '%s'\n", outputFile);
        fclose(input);
        return EXIT_FAILURE;
    }

    while ((bytesRead = fread(buffer, 1, BUFFER_SIZE, input)) > 0) {
        fwrite(buffer, 1, bytesRead, output);
    }

    printf("File copied successfully from '%s' to '%s'\n", inputFile, outputFile);

    fclose(input);
    fclose(output);

    return EXIT_SUCCESS;
}

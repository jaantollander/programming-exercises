CC := gcc
CFLAGS := -Wall

main: main.o
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

main.o: main.c
	$(CC) -c $(CPPFLAGS) $(CFLAGS) $^ -o $@

.PHONY: clean
clean:
	rm main.o main

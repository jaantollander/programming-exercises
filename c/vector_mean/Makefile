BUILD_DIR := ./build
SRC_DIR := ./src

CC := gcc
CFLAGS := -Wall -fpic -shared

$(BUILD_DIR)/mean.so: $(SRC_DIR)/mean.c
	mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $^ -o $@

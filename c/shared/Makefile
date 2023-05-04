BUILD_DIR := ./build
SRC_DIR := ./src

CC := gcc
CFLAGS := -Wall -Werror -fpic
LDFLAGS := -L $(shell pwd)/$(BUILD_DIR)

$(BUILD_DIR)/main: $(SRC_DIR)/main.c $(BUILD_DIR)/main.so
	mkdir -p $(dir $@)
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

$(BUILD_DIR)/main.so: $(BUILD_DIR)/main.o
	mkdir -p $(dir $@)
	$(CC) $^ -o $@ -shared

$(BUILD_DIR)/main.o: $(SRC_DIR)/main.c
	mkdir -p $(dir $@)
	$(CC) -c $(CPPFLAGS) $(CFLAGS) $^ -o $@

.PHONY: clean
clean:
	rm -r $(BUILD_DIR)

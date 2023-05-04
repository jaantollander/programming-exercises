BUILD_DIR := ./build
SRC_DIR := ./src

CC := gcc
CFLAGS := -Wall -Werror

$(BUILD_DIR)/main: $(BUILD_DIR)/main.o
	mkdir -p $(dir $@)
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

$(BUILD_DIR)/main.o: $(SRC_DIR)/main.c
	mkdir -p $(dir $@)
	$(CC) -c $(CPPFLAGS) $(CFLAGS) $^ -o $@

.PHONY: clean
clean:
	rm -r $(BUILD_DIR)

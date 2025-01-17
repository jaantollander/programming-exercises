package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
)

// User struct to represent user data
type User struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

// CreateUserRequest struct for incoming user creation request
type CreateUserRequest struct {
	Name  string `json:"name"`
	Email string `json:"email"`
}

// Global slice to simulate a simple in-memory database
var users = []User{
	{ID: 1, Name: "John Doe", Email: "john@example.com"},
	{ID: 2, Name: "Jane Smith", Email: "jane@example.com"},
}

// Handler for creating a new user
func createUserHandler(w http.ResponseWriter, r *http.Request) {
	// Ensure only POST method is accepted
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Read the request body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Error reading request body", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// Parse the incoming JSON
	var newUserReq CreateUserRequest
	err = json.Unmarshal(body, &newUserReq)
	if err != nil {
		http.Error(w, "Error parsing JSON", http.StatusBadRequest)
		return
	}

	// Create a new user
	newUser := User{
		ID:    len(users) + 1,
		Name:  newUserReq.Name,
		Email: newUserReq.Email,
	}

	// Add user to the "database"
	users = append(users, newUser)

	// Set response headers
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)

	// Convert user to JSON and send response
	json.NewEncoder(w).Encode(newUser)
}

// Handler for getting all users
func getUsersHandler(w http.ResponseWriter, r *http.Request) {
	// Ensure only GET method is accepted
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Set response headers
	w.Header().Set("Content-Type", "application/json")

	// Convert users to JSON and send response
	json.NewEncoder(w).Encode(users)
}

func main() {
	// Define routes
	http.HandleFunc("/users", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			getUsersHandler(w, r)
		case http.MethodPost:
			createUserHandler(w, r)
		default:
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	})

	// Start the server
	port := 8000
	fmt.Printf("Server starting on port %d...\n", port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}

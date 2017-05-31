package main

import (
	"net/http"
	"encoding/json"
	"log"
	"github.com/jlaffaye/ftp"
	"github.com/gorilla/mux"
	"fmt"
	"time"
	"os"
	"io"
	"path/filepath"
)

type HealthCheck struct {
	Status string
	Ftp string
}

func healthCheck(w http.ResponseWriter, _ *http.Request) {
	ok := "OK"
	failed := "FAILED"
	var status, ftpStatus = ok, ok


	if !checkFtp() {
		status, ftpStatus = failed, failed
	}

	response, err := json.Marshal(&HealthCheck{status, ftpStatus})
	if err != nil {
		log.Print(err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	w.Write(response)
}

func uploadFile(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	id := params["id"]
	filename := params["filename"]
	log.Printf("Received file %s for collection exercise %s", filename, id)

	infile, header, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "Error uploading file: " + err.Error(), http.StatusBadRequest)
		return
	}
	directory := filepath.Join("./uploaded/bres/", id)

	if _, err := os.Stat(directory); os.IsNotExist(err) {
		os.MkdirAll(directory, os.ModePerm)
	}

	file := filepath.Join(directory, header.Filename)
	outfile, err := os.Create(file)
	if err != nil {
		http.Error(w, "Error saving file: "+err.Error(), http.StatusBadRequest)
		return
	}

	_, err = io.Copy(outfile, infile)
	if err != nil {
		http.Error(w, "Error saving file: "+err.Error(), http.StatusBadRequest)
		return
	}
	fmt.Fprint(w, "OK")
}


func checkFtp() bool {
	conn, err := connectToFtp()
	if err != nil {
		log.Print("FTP healthcheck failed")
	} else {
		log.Print("FTP healthcheck sucessful")
		defer conn.Logout()
	}

	return err == nil
}

func connectToFtp() (*ftp.ServerConn, error) {
	conn, err := ftp.Connect("localhost:2021")
	if err != nil {
		log.Print(err)
		return nil, err
	}
	conn.Login("ons", "ons")
	return conn, err
}


func main() {
	r := mux.NewRouter()
	r.HandleFunc("/healthcheck", healthCheck)
	r.HandleFunc("/upload/{id}/{filename}", uploadFile).Methods("POST")

	server := &http.Server{
		Handler:      r,
		Addr:         "0.0.0.0:8091",
		WriteTimeout: 15 * time.Second,
		ReadTimeout:  15 * time.Second,
	}

	log.Fatal(server.ListenAndServe())
}

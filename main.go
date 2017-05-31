package main

import (
	"encoding/json"
	"fmt"
	"log"
	"mime/multipart"
	"net/http"
	"time"
	"github.com/warrenbailey/ftp"
	"github.com/gorilla/mux"
)

type HealthCheck struct {
	Status string
	Ftp string
}

const ok = "OK"
const failed = "FAILED"

func healthCheck(w http.ResponseWriter, _ *http.Request) {
	var status, ftpStatus = ok, ok
	if _, err := connectToFtp(); err != nil {
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
	err = transferToFtp(infile, header, id)
	if err != nil {
		http.Error(w, "Error uploading file: " + err.Error(), http.StatusInternalServerError)
		return
	}
	fmt.Fprint(w, "OK")
}

func transferToFtp(file multipart.File, header *multipart.FileHeader, directory string) error {
	conn, err  := connectToFtp()
	if err != nil {
		log.Print("Unable to connect to FTP")
		return err
	}
	err = conn.ChangeDir(directory)
	if err != nil {
		log.Print("Unable to change directory on FTP - attempting to create")
		err = conn.MakeDir(directory)
		if err != nil {
			log.Print("Unable to create directory on FTP")
			return err
		}
		err = conn.ChangeDir(directory)
		if err != nil {
			log.Print("Unable to change directory on FTP")
			return err
		}
	}
	err = conn.Stor(header.Filename, file)
	if err != nil {
		log.Print("Unable to store file on to FTP")
		return err
	}
	return nil
}

func connectToFtp() (*ftp.ServerConn, error) {
	conn, err := ftp.Connect("localhost:2021")
	if err != nil {
		log.Print("Failed to connect to FTP server", err)
		return nil, err
	}
	err = conn.Login("ons-inbound", "ons-inbound")
	if err != nil {
		log.Print("Error login into FTP server: ", err)
	}
	err = conn.Binary()
	if err != nil {
		log.Print("Unable to switch to binary mode: ", err)
	}
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

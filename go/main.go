package main

import (
    "encoding/json"
    "log"
    "net/http"
)

type QueryRequest struct {
    Query string `json:"query"`
}

type QueryResponse struct {
    TraceID string `json:"trace_id"`
    Status  string `json:"status"`
    Answer  string `json:"answer"`
}

func queryHandler(w http.ResponseWriter, r *http.Request) {
    decoder := json.NewDecoder(r.Body)
    var req QueryRequest
    if err := decoder.Decode(&req); err != nil {
        http.Error(w, "bad request", http.StatusBadRequest)
        return
    }
    resp := QueryResponse{TraceID: "go-demo", Status: "success", Answer: "Go variant processed: " + req.Query}
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(resp)
}

func main() {
    http.HandleFunc("/v1/query", queryHandler)
    http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("ok")) })
    log.Println("Go variant listening on :9000")
    log.Fatal(http.ListenAndServe(":9000", nil))
}

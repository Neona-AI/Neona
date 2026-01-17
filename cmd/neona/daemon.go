package main

import (
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"

	"github.com/fentz26/neona/internal/audit"
	"github.com/fentz26/neona/internal/connectors/localexec"
	"github.com/fentz26/neona/internal/controlplane"
	"github.com/fentz26/neona/internal/store"
	"github.com/spf13/cobra"
)

var (
	listenAddr string
	dbPath     string
)

var daemonCmd = &cobra.Command{
	Use:   "daemon",
	Short: "Start the Neona daemon (neonad)",
	Long:  `Starts the Neona daemon which provides the HTTP API for task coordination.`,
	RunE:  runDaemon,
}

func init() {
	homeDir, _ := os.UserHomeDir()
	defaultDB := filepath.Join(homeDir, ".neona", "neona.db")

	daemonCmd.Flags().StringVar(&listenAddr, "listen", "127.0.0.1:7466", "Listen address for the API server")
	daemonCmd.Flags().StringVar(&dbPath, "db", defaultDB, "Path to SQLite database")
}

func runDaemon(cmd *cobra.Command, args []string) error {
	log.Println("Starting Neona daemon...")

	// Initialize store
	s, err := store.New(dbPath)
	if err != nil {
		return err
	}
	defer s.Close()

	// Initialize components
	pdr := audit.NewPDRWriter(s)
	workDir, _ := os.Getwd()
	connector := localexec.New(workDir)

	// Create service and server
	service := controlplane.NewService(s, pdr, connector)
	server := controlplane.NewServer(service, listenAddr)

	// Handle graceful shutdown
	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		log.Println("Shutting down...")
		os.Exit(0)
	}()

	// Start server
	return server.Start()
}

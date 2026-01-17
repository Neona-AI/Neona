package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "neona",
	Short: "Neona - AI Control Plane CLI",
	Long:  `Neona is a CLI-centric AI Control Plane that coordinates multiple AI tools under shared rules, knowledge, and policy.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Default to running TUI
		return runTUI(cmd, args)
	},
}

var (
	apiAddr string
)

func init() {
	rootCmd.PersistentFlags().StringVar(&apiAddr, "api", "http://127.0.0.1:7466", "API server address")

	// Add subcommands
	rootCmd.AddCommand(daemonCmd)
	rootCmd.AddCommand(taskCmd)
	rootCmd.AddCommand(memoryCmd)
	rootCmd.AddCommand(tuiCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

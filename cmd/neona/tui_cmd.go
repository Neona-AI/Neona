package main

import (
	"fmt"

	"github.com/fentz26/neona/internal/tui"
	"github.com/spf13/cobra"
)

var tuiCmd = &cobra.Command{
	Use:   "tui",
	Short: "Launch the interactive TUI",
	RunE:  runTUI,
}

func runTUI(cmd *cobra.Command, args []string) error {
	app := tui.New(apiAddr)
	if err := app.Run(); err != nil {
		return fmt.Errorf("TUI error: %w", err)
	}
	return nil
}

package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
)

var (
	fullUninstall bool
	keepData      bool
)

var uninstallCmd = &cobra.Command{
	Use:   "uninstall",
	Short: "Uninstall Neona CLI and optionally remove data",
	Long:  `Uninstall the Neona CLI binary and optionally remove the configuration/data directory (~/.neona).`,
	RunE:  runUninstall,
}

func init() {
	uninstallCmd.Flags().BoolVar(&fullUninstall, "full", false, "Remove both binary and all data (~/.neona) without prompting")
	uninstallCmd.Flags().BoolVar(&keepData, "keep-data", false, "Remove binary but keep data (skip prompt)")

	rootCmd.AddCommand(uninstallCmd)
}

func runUninstall(cmd *cobra.Command, args []string) error {
	binPath, err := os.Executable()
	if err != nil {
		return fmt.Errorf("failed to determine executable path: %w", err)
	}

	// Resolve symlink if possible, just for display/info.
	// We want to delete the actual file we are running.
	// If it was a symlink, os.Executable usually returns the target.
	evalPath, err := filepath.EvalSymlinks(binPath)
	if err == nil {
		binPath = evalPath
	}

	homeDir, err := os.UserHomeDir()
	if err != nil {
		return fmt.Errorf("failed to get home directory: %w", err)
	}
	dataDir := filepath.Join(homeDir, ".neona")

	var removeData bool

	// Determine mode
	if fullUninstall {
		removeData = true
	} else if keepData {
		removeData = false
	} else {
		// Interactive Prompt
		fmt.Println("⚠️  Neona Uninstaller")
		fmt.Printf("   Binary Location: %s\n", binPath)
		fmt.Printf("   Data Location:   %s\n", dataDir)
		fmt.Println("")

		reader := bufio.NewReader(os.Stdin)

		// Ask for confirmation
		fmt.Print("Are you sure you want to uninstall Neona? [y/N]: ")
		confirm, _ := reader.ReadString('\n')
		if strings.ToLower(strings.TrimSpace(confirm)) != "y" {
			fmt.Println("Uninstall aborted.")
			return nil
		}

		// Ask about data
		fmt.Printf("Do you also want to delete all data (skills, agents, logs, etc.) in %s? [y/N]: ", dataDir)
		dataConfirm, _ := reader.ReadString('\n')
		if strings.ToLower(strings.TrimSpace(dataConfirm)) == "y" {
			removeData = true
		}
	}

	// Perform Uninstall
	fmt.Println("\n🗑️  Uninstalling...")

	// 1. Remove Data (if requested)
	if removeData {
		fmt.Printf("   Removing data directory (%s)... ", dataDir)
		if err := os.RemoveAll(dataDir); err != nil {
			fmt.Printf("Failed: %v\n", err)
		} else {
			fmt.Println("Done")
		}
	} else {
		fmt.Println("   Keeping data directory.")
	}

	// 2. Remove Binary
	fmt.Printf("   Removing binary (%s)... ", binPath)
	if err := os.Remove(binPath); err != nil {
		fmt.Printf("Failed: %v\n", err)
		if os.IsPermission(err) {
			fmt.Println("   ❌ Permission denied. You might need to run this command with 'sudo'.")
			fmt.Println("   Try: sudo neona uninstall")
		}
	} else {
		fmt.Println("Done")
	}

	fmt.Println("\n✅ Neona has been uninstalled.")
	return nil
}

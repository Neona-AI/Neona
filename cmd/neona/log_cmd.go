package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

var (
	logFollow  bool
	logLines   int
	logService string
	logLevel   string
)

var logCmd = &cobra.Command{
	Use:   "log",
	Short: "Show Neona daemon logs",
	Long: `Display the Neona daemon logs to check for errors and debug issues.

By default, shows the last 50 lines from the daemon log file.
Use --follow (-f) to continuously stream new log entries.

Examples:
  neona log                    # Show last 50 lines
  neona log -n 100             # Show last 100 lines
  neona log -f                 # Follow/tail the log
  neona log --level error      # Show only error logs`,
	RunE: runLog,
}

func init() {
	logCmd.Flags().BoolVarP(&logFollow, "follow", "f", false, "Follow log output (like tail -f)")
	logCmd.Flags().IntVarP(&logLines, "lines", "n", 50, "Number of lines to show")
	logCmd.Flags().StringVar(&logService, "service", "", "Filter by service (daemon, scheduler, mcp)")
	logCmd.Flags().StringVar(&logLevel, "level", "", "Filter by level (error, warning, info)")
}

func getLogPath() (string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get home directory: %w", err)
	}
	return filepath.Join(homeDir, ".neona", "neona.log"), nil
}

func runLog(cmd *cobra.Command, args []string) error {
	logPath, err := getLogPath()
	if err != nil {
		return err
	}

	// Check if log file exists
	if _, err := os.Stat(logPath); os.IsNotExist(err) {
		// No log file, show message and check if daemon logs exist in journald
		fmt.Printf("📋 Log file not found at: %s\n\n", logPath)
		fmt.Println("The daemon may be logging to stdout/stderr. To capture logs:")
		fmt.Println("")
		fmt.Println("  1. Run 'neona daemon' in a terminal to see live output")
		fmt.Println("  2. Or redirect output: neona daemon > ~/.neona/neona.log 2>&1 &")
		fmt.Println("")
		fmt.Println("If running via systemd, check with: journalctl -u neona")
		return nil
	}

	if logFollow {
		return tailLog(logPath)
	}

	return showRecentLogs(logPath)
}

func showRecentLogs(logPath string) error {
	file, err := os.Open(logPath)
	if err != nil {
		return fmt.Errorf("failed to open log file: %w", err)
	}
	defer file.Close()

	// Read all lines first
	var lines []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		if shouldShowLine(line) {
			lines = append(lines, line)
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("error reading log file: %w", err)
	}

	// Get last N lines
	start := 0
	if len(lines) > logLines {
		start = len(lines) - logLines
	}

	if len(lines) == 0 {
		fmt.Println("📋 No log entries found")
		if logLevel != "" {
			fmt.Printf("   (filtered by level: %s)\n", logLevel)
		}
		return nil
	}

	fmt.Printf("📋 Showing last %d log entries from %s\n", min(logLines, len(lines)), logPath)
	fmt.Println(strings.Repeat("─", 60))

	for i := start; i < len(lines); i++ {
		printColoredLog(lines[i])
	}

	fmt.Println(strings.Repeat("─", 60))
	fmt.Printf("📊 Total: %d entries shown\n", len(lines)-start)

	return nil
}

func tailLog(logPath string) error {
	file, err := os.Open(logPath)
	if err != nil {
		return fmt.Errorf("failed to open log file: %w", err)
	}
	defer file.Close()

	// Seek to end of file
	_, err = file.Seek(0, 2)
	if err != nil {
		return fmt.Errorf("failed to seek to end of file: %w", err)
	}

	fmt.Printf("📋 Following log file: %s (Ctrl+C to stop)\n", logPath)
	fmt.Println(strings.Repeat("─", 60))

	reader := bufio.NewReader(file)
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			// No new data, wait and retry
			time.Sleep(100 * time.Millisecond)
			continue
		}

		line = strings.TrimSuffix(line, "\n")
		if shouldShowLine(line) {
			printColoredLog(line)
		}
	}
}

func shouldShowLine(line string) bool {
	// Filter by log level if specified
	if logLevel != "" {
		lowerLine := strings.ToLower(line)
		switch strings.ToLower(logLevel) {
		case "error":
			if !strings.Contains(lowerLine, "error") && !strings.Contains(lowerLine, "fatal") {
				return false
			}
		case "warning", "warn":
			if !strings.Contains(lowerLine, "warn") && !strings.Contains(lowerLine, "error") && !strings.Contains(lowerLine, "fatal") {
				return false
			}
		case "info":
			// Show all for info
		}
	}

	// Filter by service if specified
	if logService != "" {
		lowerLine := strings.ToLower(line)
		if !strings.Contains(lowerLine, strings.ToLower(logService)) {
			return false
		}
	}

	return true
}

func printColoredLog(line string) {
	lowerLine := strings.ToLower(line)

	// Colorize based on content
	if strings.Contains(lowerLine, "error") || strings.Contains(lowerLine, "fatal") {
		// Red for errors
		fmt.Printf("\033[31m%s\033[0m\n", line)
	} else if strings.Contains(lowerLine, "warn") {
		// Yellow for warnings
		fmt.Printf("\033[33m%s\033[0m\n", line)
	} else if strings.Contains(lowerLine, "success") || strings.Contains(lowerLine, "started") || strings.Contains(lowerLine, "complete") {
		// Green for success
		fmt.Printf("\033[32m%s\033[0m\n", line)
	} else {
		// Default
		fmt.Println(line)
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

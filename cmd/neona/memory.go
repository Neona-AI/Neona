package main

import (
	"encoding/json"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/spf13/cobra"
)

var memoryCmd = &cobra.Command{
	Use:   "memory",
	Short: "Manage memory items",
}

var memoryAddCmd = &cobra.Command{
	Use:   "add",
	Short: "Add a memory item",
	RunE:  runMemoryAdd,
}

var memoryQueryCmd = &cobra.Command{
	Use:   "query",
	Short: "Query memory items",
	RunE:  runMemoryQuery,
}

var (
	memContent string
	memTags    string
	memTaskID  string
	memQuery   string
)

func init() {
	memoryCmd.AddCommand(memoryAddCmd, memoryQueryCmd)

	memoryAddCmd.Flags().StringVar(&memContent, "content", "", "Memory content (required)")
	memoryAddCmd.Flags().StringVar(&memTags, "tags", "", "Comma-separated tags")
	memoryAddCmd.Flags().StringVar(&memTaskID, "task", "", "Associated task ID")
	memoryAddCmd.MarkFlagRequired("content")

	memoryQueryCmd.Flags().StringVar(&memQuery, "q", "", "Search query")
}

func runMemoryAdd(cmd *cobra.Command, args []string) error {
	body := map[string]string{
		"content": memContent,
		"tags":    memTags,
		"task_id": memTaskID,
	}

	resp, err := apiPost("/memory", body)
	if err != nil {
		return err
	}

	var result map[string]interface{}
	if err := json.Unmarshal(resp, &result); err != nil {
		return err
	}

	fmt.Printf("Created memory item: %s\n", result["id"])
	return nil
}

func runMemoryQuery(cmd *cobra.Command, args []string) error {
	url := "/memory"
	if memQuery != "" {
		url += "?q=" + memQuery
	}

	resp, err := apiGet(url)
	if err != nil {
		return err
	}

	var items []map[string]interface{}
	if err := json.Unmarshal(resp, &items); err != nil {
		return err
	}

	if len(items) == 0 {
		fmt.Println("No memory items found")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "ID\tTASK\tCONTENT\tTAGS")
	for _, item := range items {
		id := truncateID(item["id"].(string))
		taskID := ""
		if tid, ok := item["task_id"].(string); ok {
			taskID = truncateID(tid)
		}
		content := truncate(item["content"].(string), 50)
		tags := ""
		if t, ok := item["tags"].(string); ok {
			tags = t
		}
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\n", id, taskID, content, tags)
	}
	w.Flush()
	return nil
}

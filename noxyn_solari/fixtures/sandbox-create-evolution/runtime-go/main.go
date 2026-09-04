// Controlled aligned Go consumer used by the runtime verification fixture.
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	solari "github.com/solari-sdk/solari-sandbox-go"
)

func main() {
	ctx := context.Background()
	client, err := solari.NewClient(solari.ClientOptions{
		APIKey:  os.Getenv("SOLARI_API_KEY"),
		BaseURL: os.Getenv("SOLARI_API_BASE_URL"),
	})
	if err != nil {
		log.Fatal(err)
	}
	subject, err := client.Create(ctx, solari.CreateOptions{
		Template: "base",
		MemMb:    2048,
	})
	if err != nil {
		log.Fatal(err)
	}
	defer func() {
		if err := subject.Kill(ctx); err != nil {
			log.Fatal("nested subject cleanup failed: ", err)
		}
	}()
	fmt.Println("Go Sandbox.Create(CreateOptions{MemMb}) succeeded.")
}

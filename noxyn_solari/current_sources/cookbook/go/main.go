package main

import solari "github.com/solari-sdk/solari-sandbox-go"

func create(client *solari.Client) {
	client.Create(nil, solari.CreateOptions{Template: "base", MemMb: 2048})
}

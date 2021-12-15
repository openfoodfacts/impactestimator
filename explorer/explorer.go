//go:generate pkger
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"

	"github.com/markbates/pkger"
)

func mustParseJSON(s string, i interface{}) {
	if err := json.Unmarshal([]byte(s), i); err != nil {
		panic(err)
	}
}

type server struct {
	ingredients map[string]map[string]interface{}
	products    map[string]map[string]interface{}
	agriBalyse  map[string]map[string]interface{}
	index       []byte
}

type metadataRequest struct {
	CIQUALCode  string
	Ingredients []string
}

type metadataResponse struct {
	ProductName        string
	Ingredients        []map[string]float64
	ImpactByIngredient map[string]float64
}

func (s *server) handleMetadata(w http.ResponseWriter, r *http.Request) {
	mreq := &metadataRequest{}
	if err := json.NewDecoder(r.Body).Decode(mreq); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	mresp := &metadataResponse{
		ImpactByIngredient: map[string]float64{},
	}

	if prod, found := s.products[mreq.CIQUALCode]; found {
		// Try to find the product in the test set provided by Gustave.
		mresp.ProductName = prod["product_name"].(string)
		for _, ingredIf := range prod["ingredients"].([]interface{}) {
			ingred := ingredIf.(map[string]interface{})
			mresp.Ingredients = append(mresp.Ingredients, map[string]float64{
				ingred["id"].(string): ingred["percent"].(float64),
			})
			if ingred, found := s.ingredients[ingred["id"].(string)]; found {
				if impact, found := ingred["impacts"].(map[string]interface{})["Score unique EF"]; found {
					mresp.ImpactByIngredient[ingred["id"].(string)] = impact.(map[string]interface{})["amount"].(float64)
				}
			}
		}
	} else if prod, found := s.agriBalyse[mreq.CIQUALCode]; found {
		// Try to find the product in the AgriBalyse JSON.
		mresp.ProductName = prod["nom_francais"].(string)
		if impacts, found := prod["impact_environnemental"]; found {
			if efImpacts, found := impacts.(map[string]interface{})["Score unique EF"]; found {
				if ingredients, found := efImpacts.(map[string]interface{})["ingredients"]; found {
					ingredientsMap := ingredients.(map[string]interface{})
					for ingID, impact := range ingredientsMap {
						mresp.Ingredients = append(mresp.Ingredients, map[string]float64{
							ingID: 1.0,
						})
						mresp.ImpactByIngredient[ingID] = impact.(float64)
					}
				}
			}
		}
	}
	for _, ingredID := range mreq.Ingredients {
		if ingred, found := s.ingredients[ingredID]; found {
			if impact, found := ingred["impacts"]; found {
				if efImpact, found := impact.(map[string]interface{})["Score unique EF"]; found {
					mresp.ImpactByIngredient[ingredID] = efImpact.(map[string]interface{})["amount"].(float64)
				}
			}
		}
	}

	if err := json.NewEncoder(w).Encode(mresp); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

func (s *server) handle(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" && r.URL.Path == "/metadata" {
		s.handleMetadata(w, r)
	} else if r.Method == "GET" && r.URL.Path == "/codes" {
		s.handleKnownCodes(w, r)
	} else {
		s.handleIndex(w, r)
	}
}

func (s *server) handleKnownCodes(w http.ResponseWriter, r *http.Request) {
	resp := map[string]bool{}
	for k := range s.products {
		resp[k] = true
	}
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

func (s *server) handleIndex(w http.ResponseWriter, r *http.Request) {
	if _, err := w.Write(s.index); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

func (s *server) mustDecodeJSON(path string, i interface{}) {
	f, err := pkger.Open(path)
	if err != nil {
		panic(err)
	}
	defer f.Close()
	if err := json.NewDecoder(f).Decode(i); err != nil {
		panic(err)
	}
}

func newServer() *server {
	s := &server{
		products:    map[string]map[string]interface{}{},
		ingredients: map[string]map[string]interface{}{},
		agriBalyse:  map[string]map[string]interface{}{},
	}

	products := []map[string]interface{}{}
	s.mustDecodeJSON("/binary/products.json", &products)
	for idx := range products {
		s.products[products[idx]["ciqual_code"].(string)] = products[idx]
	}

	agriBalyseProducts := []map[string]interface{}{}
	s.mustDecodeJSON("/binary/Agribalyse.json", &agriBalyseProducts)
	for idx := range agriBalyseProducts {
		s.agriBalyse[agriBalyseProducts[idx]["ciqual_code"].(string)] = agriBalyseProducts[idx]
	}

	s.mustDecodeJSON("/binary/ingredients.json", &s.ingredients)

	f, err := pkger.Open("/binary/index.html")
	if err != nil {
		panic(err)
	}
	if s.index, err = ioutil.ReadAll(f); err != nil {
		panic(err)
	}

	return s
}

func main() {
	port := flag.Int("port", 8080, "Port to listen to.")
	flag.Parse()

	s := newServer()

	fmt.Printf("Listening on %v\n", *port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%v", *port), http.HandlerFunc(s.handle)))
}

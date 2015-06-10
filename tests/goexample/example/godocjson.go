package main

import (
	"encoding/json"
	"fmt"
	"go/doc"
	"go/parser"
	"go/token"
	"os"
)

// Func represents a function declaration.
type Func struct {
	Doc               string `json:"doc"`
	Name              string `json:"name"`
	PackageName       string `json:"packageName"`
	PackageImportPath string `json:"packageImportPath"`
	// Decl              *ast.FuncDecl

	// methods
	// (for functions, these fields have the respective zero value)
	Recv string `json:"recv"` // actual   receiver "T" or "*T"
	Orig string `json:"orig"` // original receiver "T" or "*T"
	// Level int    // embedding level; 0 means not embedded
}

// Package represents a package declaration.
type Package struct {
	Type       string             `json:"type"`
	Doc        string             `json:"doc"`
	Name       string             `json:"name"`
	ImportPath string             `json:"importPath"`
	Imports    []string           `json:"imports"`
	Filenames  []string           `json:"filenames"`
	Notes      map[string][]*Note `json:"notes"`
	// DEPRECATED. For backward compatibility Bugs is still populated,
	// but all new code should use Notes instead.
	Bugs []string `json:"bugs"`

	// declarations
	Consts []*Value `json:"consts"`
	Types  []*Type  `json:"types"`
	Vars   []*Value `json:"vars"`
	Funcs  []*Func  `json:"funcs"`
}

// Note represents a note comment.
type Note struct {
	Pos  token.Pos `json:"pos"`
	End  token.Pos `json:"end"`  // position range of the comment containing the marker
	UID  string    `json:"uid"`  // uid found with the marker
	Body string    `json:"body"` // note body text
}

// Type represents a type declaration.
type Type struct {
	PackageName       string `json:"packageName"`
	PackageImportPath string `json:"packageImportPath"`
	Doc               string `json:"doc"`
	Name              string `json:"name"`
	// Decl              *ast.GenDecl

	// associated declarations
	Consts  []*Value `json:"consts"`  // sorted list of constants of (mostly) this type
	Vars    []*Value `json:"vars"`    // sorted list of variables of (mostly) this type
	Funcs   []*Func  `json:"funcs"`   // sorted list of functions returning this type
	Methods []*Func  `json:"methods"` // sorted list of methods (including embedded ones) of this type
}

// Value represents a value declaration.
type Value struct {
	PackageName       string   `json:"packageName"`
	PackageImportPath string   `json:"packageImportPath"`
	Doc               string   `json:"doc"`
	Names             []string `json:"names"` // var or const names in declaration order
	// Decl              *ast.GenDecl
}

// CopyFuncs produces a json-annotated array of Func objects from an array of GoDoc Func objects.
func CopyFuncs(f []*doc.Func, packageName string, packageImportPath string) []*Func {
	newFuncs := make([]*Func, len(f))
	for i, n := range f {
		newFuncs[i] = &Func{
			Doc:               n.Doc,
			Name:              n.Name,
			PackageName:       packageName,
			PackageImportPath: packageImportPath,
			Orig:              n.Orig,
			Recv:              n.Recv,
		}
	}
	return newFuncs
}

// CopyValues produces a json-annotated array of Value objects from an array of GoDoc Value objects.
func CopyValues(c []*doc.Value, packageName string, packageImportPath string) []*Value {
	newConsts := make([]*Value, len(c))
	for i, c := range c {
		newConsts[i] = &Value{
			Doc:               c.Doc,
			Names:             c.Names,
			PackageName:       packageName,
			PackageImportPath: packageImportPath,
		}
	}
	return newConsts
}

// CopyPackage produces a json-annotated Package object from a GoDoc Package object.
func CopyPackage(pkg *doc.Package) Package {
	newPkg := Package{
		Type:       "package",
		Doc:        pkg.Doc,
		Name:       pkg.Name,
		ImportPath: pkg.ImportPath,
		Imports:    pkg.Imports,
		Filenames:  pkg.Filenames,
		Bugs:       pkg.Bugs,
	}

	newPkg.Notes = map[string][]*Note{}
	for key, value := range pkg.Notes {
		notes := make([]*Note, len(value))
		for i, note := range value {
			notes[i] = &Note{
				Pos:  note.Pos,
				End:  note.End,
				UID:  note.UID,
				Body: note.Body,
			}
		}
		newPkg.Notes[key] = notes
	}

	newPkg.Consts = CopyValues(pkg.Consts, pkg.Name, pkg.ImportPath)
	newPkg.Funcs = CopyFuncs(pkg.Funcs, pkg.Name, pkg.ImportPath)

	newPkg.Types = make([]*Type, len(pkg.Types))
	for i, t := range pkg.Types {
		newPkg.Types[i] = &Type{
			Name:              t.Name,
			PackageName:       pkg.Name,
			PackageImportPath: pkg.ImportPath,
			Consts:            CopyValues(t.Consts, pkg.Name, pkg.ImportPath),
			Doc:               t.Doc,
			Funcs:             CopyFuncs(t.Funcs, pkg.Name, pkg.ImportPath),
			Methods:           CopyFuncs(t.Methods, pkg.Name, pkg.ImportPath),
			Vars:              CopyValues(t.Vars, pkg.Name, pkg.ImportPath),
		}
	}

	newPkg.Vars = CopyValues(pkg.Vars, pkg.Name, pkg.ImportPath)
	return newPkg
}

func main() {
	directories := os.Args[1:]
	for _, dir := range directories {
		fileSet := token.NewFileSet()
		pkgs, firstError := parser.ParseDir(fileSet, dir, nil, parser.ParseComments|parser.AllErrors)
		if firstError != nil {
			panic(firstError)
		}
		for _, pkg := range pkgs {
			docPkg := doc.New(pkg, dir, 0)
			cleanedPkg := CopyPackage(docPkg)
			pkgJSON, err := json.MarshalIndent(cleanedPkg, "", "  ")
			if err != nil {
				panic(err)
			}
			fmt.Printf("%s\n", pkgJSON)
		}
	}
}

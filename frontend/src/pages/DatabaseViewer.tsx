import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Database, AlertTriangle } from "lucide-react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

interface TableData {
  columns: string[];
  rows: Record<string, any>[];
}

type AllTablesData = Record<string, TableData>;

const fetchAllTables = async (): Promise<AllTablesData> => {
  const response = await fetch("/api/database/tables");
  if (!response.ok) {
    throw new Error("Network response was not ok");
  }
  const jsonResponse = await response.json();
  if (!jsonResponse.success) {
    throw new Error(jsonResponse.error || "Failed to fetch table data");
  }
  return jsonResponse.data;
};

const DatabaseViewer = () => {
  const [selectedTable, setSelectedTable] = useState<string>("");

  const {
    data: allTables,
    isLoading,
    isError,
    error,
  } = useQuery<AllTablesData>({
    queryKey: ["databaseTables"],
    queryFn: fetchAllTables,
    staleTime: Infinity, // This data is structural, no need to refetch often
  });

  const tableNames = allTables ? Object.keys(allTables) : [];
  const currentTableData = allTables && selectedTable ? allTables[selectedTable] : null;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Database /> Database Viewer
          </h1>
          <p className="text-muted-foreground">
            Inspect tables and data from the application database.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select a Table to View</CardTitle>
          <Select onValueChange={setSelectedTable} value={selectedTable}>
            <SelectTrigger className="w-full md:w-72 mt-2">
              <SelectValue placeholder={isLoading ? "Loading tables..." : "Select a table"} />
            </SelectTrigger>
            <SelectContent>
              {tableNames.map((name) => (
                <SelectItem key={name} value={name}>
                  {name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent>
          {isLoading && <div className="flex justify-center items-center h-40"><Loader2 className="h-8 w-8 animate-spin" /></div>}
          {isError && <div className="text-destructive flex items-center gap-2"><AlertTriangle /> Error: {error.message}</div>}
          
          {currentTableData && (
            <ScrollArea className="w-full whitespace-nowrap rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    {currentTableData.columns.map((col) => (
                      <TableHead key={col}>{col}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentTableData.rows.length > 0 ? (
                    currentTableData.rows.map((row, rowIndex) => (
                      <TableRow key={rowIndex}>
                        {currentTableData.columns.map((col) => (
                          <TableCell key={`${rowIndex}-${col}`}>{String(row[col])}</TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={currentTableData.columns.length} className="h-24 text-center">No rows found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
              <ScrollBar orientation="horizontal" />
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DatabaseViewer;

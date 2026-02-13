import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import type { ValidationItem } from "@/types";

interface ValidationResultProps {
  totalRows: number;
  errors: ValidationItem[];
  warnings: ValidationItem[];
}

export function ValidationResult({ totalRows, errors, warnings }: ValidationResultProps) {
  const isValid = errors.length === 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 pb-3">
        {isValid ? (
          <CheckCircle2 className="h-5 w-5 text-green-600" />
        ) : (
          <XCircle className="h-5 w-5 text-red-600" />
        )}
        <CardTitle className="text-base">
          검증 결과: {totalRows}행 {isValid ? "통과" : "실패"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {errors.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1 text-sm font-medium text-red-600">
              <XCircle className="h-4 w-4" /> 오류 ({errors.length})
            </h4>
            <ul className="space-y-1 text-sm">
              {errors.map((err, i) => (
                <li key={i} className="text-muted-foreground">
                  행 {err.row}: [{err.field}] {err.message}
                </li>
              ))}
            </ul>
          </div>
        )}
        {warnings.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1 text-sm font-medium text-yellow-600">
              <AlertTriangle className="h-4 w-4" /> 경고 ({warnings.length})
            </h4>
            <ul className="space-y-1 text-sm">
              {warnings.map((warn, i) => (
                <li key={i} className="text-muted-foreground">
                  행 {warn.row}: [{warn.field}] {warn.message}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

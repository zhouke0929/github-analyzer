import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Layers, Wrench, Code2 } from "lucide-react";
import type { TechStack, TechStackItem } from "@/lib/api";

interface TechStackCardProps {
  techStack: TechStack;
}

function LanguageBar({ languages }: { languages: TechStackItem[] }) {
  const colors = [
    "bg-github",
    "bg-chart-2",
    "bg-chart-3",
    "bg-chart-4",
    "bg-chart-5",
  ];

  return (
    <div className="space-y-2">
      <div className="flex h-3 rounded-full overflow-hidden bg-muted">
        {languages.map((lang, i) => (
          <div
            key={lang.name}
            className={`${colors[i % colors.length]} transition-all duration-500`}
            style={{ width: `${lang.percentage || 0}%` }}
            title={`${lang.name}: ${lang.percentage}%`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-3">
        {languages.map((lang, i) => (
          <div key={lang.name} className="flex items-center gap-1.5 text-sm">
            <div
              className={`w-2.5 h-2.5 rounded-full ${colors[i % colors.length]}`}
            />
            <span className="text-foreground">{lang.name}</span>
            <span className="text-muted-foreground">{lang.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ItemList({
  items,
  icon: Icon,
}: {
  items: TechStackItem[];
  icon: typeof Layers;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <Badge key={item.name} variant="secondary" className="text-sm py-1 px-3">
          <Icon className="w-3.5 h-3.5 mr-1.5" />
          {item.name}
          {item.version && (
            <span className="ml-1 text-muted-foreground">{item.version}</span>
          )}
        </Badge>
      ))}
    </div>
  );
}

export function TechStackCard({ techStack }: TechStackCardProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Layers className="w-5 h-5 text-github" />
          技术栈分析
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {techStack.languages.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
              <Code2 className="w-4 h-4" />
              编程语言
            </h4>
            <LanguageBar languages={techStack.languages} />
          </div>
        )}
        {techStack.frameworks.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
              <Layers className="w-4 h-4" />
              框架
            </h4>
            <ItemList items={techStack.frameworks} icon={Layers} />
          </div>
        )}
        {techStack.tools.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
              <Wrench className="w-4 h-4" />
              工具
            </h4>
            <ItemList items={techStack.tools} icon={Wrench} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
